from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import WebDriverException

import time, sys
import argparse
from colorama import Fore, Style, Back
from datetime import datetime
import logging, pathlib
from subprocess import Popen, PIPE, STDOUT
from numpy import random
from bs4 import BeautifulSoup

curFileDir = pathlib.Path(__file__).resolve().parent.absolute()
LOG_FILE = "{}/program_logs.txt".format(curFileDir)
file_handler = logging.FileHandler(filename=LOG_FILE)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
#handlers = [file_handler, stdout_handler]
handlers = [file_handler]
logging.basicConfig(handlers=handlers, encoding='utf-8', 
                    level=logging.WARNING, format='%(asctime)s %(message)s') 

BUS_FOUND = False

def getDestList():
    destList = ["Madinah", "IMC, Main Gate", "IKEA", "Al-Balad", "Red Sea Mall",
            "Mall of Arabia", "Jeddah Int'l Market", "Makkah", "DSFH", "MY CLINIC", 
            "KAEC", "DSFMC", "THUWAL", "First Clinic"]
    return destList

def logMsg(msg, type='w', printAsWell=True):
    logFunction = {
            'd': logging.debug,
            'i': logging.info,
            'w': logging.warning,
            'e': logging.error,
            'c': logging.critical
        }
    logFunction[type](msg)
    
    if printAsWell:
        print(msg)

def checkBuses(args):
    global BUS_FOUND
    destList = getDestList()
    url = "https://kaust.saptco.com.sa/"
    testTimer = 2
    destination = args.dest
    if destination not in destList:
        logging.error(Back.WHITE + Style.BRIGHT + Fore.RED)
        logging.error("Error: Destination should be one of the following")
        logging.error(destList)
        logging.error(Fore.RESET + Style.RESET_ALL)
        print()
        sys.exit(1)
        
    departureDate = args.depDate
    numPassenger = 2
    
    # print program arguments
    logMsg(Style.BRIGHT + Fore.BLACK + "Program arguments" + Style.NORMAL)
    logMsg(Fore.BLACK + "   Destination: {}".format(destination))
    logMsg(Fore.BLACK + "   Departure date: {}".format(departureDate))
    logMsg(Fore.BLACK + "   Number of passengers: {}\n".format(numPassenger))

    # setup options
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-ssl-errors=yes')
    options.add_argument('--ignore-certificate-errors')

    # create instance of remote (docker) driver
    logMsg(Fore.BLUE + "Create instance of remote (docker) driver")
    browser = webdriver.Remote(
        command_executor='http://localhost:4444/wd/hub',
        options=options
    )

    # navigate to website and click button
    logMsg(Fore.BLUE + "Visiting {} and then waiting for {} seconds".format(url, testTimer))
    browser.get(url)
    time.sleep(testTimer)

    # select destination
    destList = browser.find_element(by=By.ID, value="MainContent_SearchWindow_DDArrival")
    select = Select(destList)
    selectedItem = select.all_selected_options[0]
    logMsg(Style.BRIGHT + Fore.BLACK + "\nSelecting destination" + Style.NORMAL)
    logMsg(Fore.BLACK + "   Default selection is '{}'".format(selectedItem.text))
    logMsg(Fore.BLACK + "   Let's select {}".format(destination))
    select.select_by_visible_text(destination)
    selectedItem = select.all_selected_options[0]
    curDest = selectedItem.text
    logMsg(Fore.BLACK + "   Current selection is '{}'".format(selectedItem.text))

    # select date
    logMsg(Style.BRIGHT + Fore.BLACK + "\nSelecting departure date" + Style.NORMAL)
    dateElement = browser.find_element(by=By.ID, value="MainContent_SearchWindow_TxtDepartureDate")
    #browser.execute_script("arguments[0].value = {};".format(departureDate), dateElement)
    browser.execute_script('document.getElementById("MainContent_SearchWindow_TxtDepartureDate").value = "{}"'.format(departureDate));


    # select number of passengers
    logMsg(Style.BRIGHT + Fore.BLACK + "\nSelecting number of passengers" + Style.NORMAL)
    passengerList = browser.find_element(by=By.ID, value="MainContent_SearchWindow_DDPassngers")
    passengers = Select(passengerList)
    selectedItem = passengers.all_selected_options[0]
    logMsg(Fore.BLACK + "   Default selection is '{}'".format(selectedItem.text))
    logMsg(Fore.BLACK + "   Let's select {} passengers".format(numPassenger))
    passengers.select_by_visible_text(str(numPassenger))
    selectedItem = passengers.all_selected_options[0]
    curNumPassengers = selectedItem.text
    logMsg(Fore.BLACK + "   New selection is '{}'".format(selectedItem.text))

    # submit the form
    logMsg(Style.BRIGHT + Fore.BLUE + "\nSearching for possible buses bound for {} on {}".format(
                destination, departureDate) + Style.NORMAL)
    submitButton = browser.find_element(by=By.ID, value = "MainContent_SearchWindow_btnRun")
    submitButton.click()
    time.sleep(testTimer)

    # Wait till the results page is loaded
    timeNow = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logMsg(Fore.BLUE + "{}: Wait till the results page is loaded".format(timeNow))
    try:
        WebDriverWait(browser, 30).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#MainContent_SearchrResults_DivRound > table,#MainContent_SearchrResults_DivNoTrips")))
    except WebDriverException as ex:
        logMsg(Fore.RED + "Error: {}".format(ex), type='e')
        browser.quit()
        return 1
        
    timeNow = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logMsg(Fore.BLUE + "{}: Search page has been loaded".format(timeNow))

    # result header
    resultTable = "twoTR"
    try:
        results = browser.find_element(by=By.CLASS_NAME, value=resultTable)
        #noResults = browser.find_element(by=By.ID, value="MainContent_SearchrResults_DivNoTrips")
        #results = browser.find_element(by=By.CLASS_NAME, value="singletrip ")
        htmlText = results.get_attribute("outerHTML")
        #noResText = noResults.get_attribute("outerHTML")
    except WebDriverException as ex:
        logMsg(Fore.RED + "Error: {}".format(ex), type='e')
        return 1

    if results.text != "":
    #if htmlText.__contains__("Arrival time"):
        numRows = len(results.text.split('\n')) - 1
        print(Fore.GREEN + "\n----------------------------------------------------------")
        logMsg(Fore.GREEN + "We have found seats available for {} bus on {}".format(
            destination, departureDate))
        if numRows == 1:
            pref = "There is 1 bus"
        else:
            pref = "There are {} buses".format(numRows)
        logMsg(Style.BRIGHT + "{} available on {}".format(pref,departureDate) + Style.NORMAL)
        print(Fore.GREEN + "----------------------------------------------------------\n")
        if not BUS_FOUND:
            query = "/Applications/VLC.app/Contents/MacOS/VLC {}/../media/Jazz_10min.mp4".format(curFileDir)
            print(query)
            p = Popen(query, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        BUS_FOUND = True
    else: 
        print(Style.BRIGHT + Fore.RED + "\n----------------------------------------------------------" + Style.NORMAL)
        logMsg(Style.BRIGHT + Fore.RED + "No seats available for {} bus on {}".format(destination, departureDate) + Style.NORMAL)
        print(Style.BRIGHT + Fore.RED + "----------------------------------------------------------\n" + Style.NORMAL)
        BUS_FOUND = False
        
    logMsg(Fore.BLUE + "Closing browser")
    browser.quit()
    logMsg(Fore.BLUE + "End of bus checking script")
    print(Back.RESET)
    return 0

def keep_checking_bus_timings(args):
    while True:
        # use White background
        print(Back.WHITE + Fore.BLUE)
        # mean 10 minutes interval with 90 seconds std.dev
        long_interval = 11 * 60
        long_variation = 90
        short_interval = 20
        short_variation = 5
        status = checkBuses(args)

        if status == 0:
            sleep_sec = random.normal(long_interval, long_variation)
            logMsg(Style.BRIGHT + Back.WHITE + Fore.RED + "Sleeping {} minutes before next try".format(round(sleep_sec/60, 2)) + Style.RESET_ALL)
        else:
            sleep_sec = random.normal(short_interval, short_variation)
            logMsg(Style.BRIGHT + Back.WHITE + Fore.RED + "Quicker retry: Sleeping {} minutes before next try".format(round(sleep_sec/60, 2)) + Style.RESET_ALL)
        time.sleep(int(sleep_sec))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KAUST Bus Checker")
    parser.add_argument("-t", "--departure-date", dest="depDate", required=True, help="Departure date (must in in dd/mm/yyyy format)")
    parser.add_argument("-d", "--destination", dest="dest", required=True, help="Destination (DSFH, Madinah, Makkah, IKEA)")
    args = parser.parse_args()
    
    # start the program
    keep_checking_bus_timings(args)
    
