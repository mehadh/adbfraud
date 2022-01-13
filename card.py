import os
from re import split
from ppadb.client import Client  # What we use to connect to the Android shell
from time import sleep  # For waiting
import os  # file system
import sys  # file system
import threading
from os import getcwd, read, walk
import subprocess

adb = None
devices = None
device = None
ita = None
cards = []
number = None
email = None
emailCounter = 0
threads = []
threaded = True
dataHandler = threading.local()
cardLock = threading.Lock()
regLock = threading.Lock()
accounts = []


def setDevice(num):
    dataHandler.device = devices[num]
    dataHandler.counter = 0
    print(dataHandler.device.serial)
    # Good to go, call the main looping function here.
    # adb pull $(adb shell uiautomator dump | grep -oP '[^ ]+.xml') /tmp/view.xml
    main()


def getCard(goMain=False):
    try:
        print("Card lock acquired")
        cardLock.acquire()
        # print(len(cards))
        currentCard = cards[0]
        cards.pop(0)
        splitCard = currentCard.split('|')
        # print(len(splitCard))
        dataHandler.cNum = splitCard[0]
        dataHandler.cMonth = splitCard[1]
        dataHandler.cYear = splitCard[2]
        dataHandler.cCvv = splitCard[3]
        dataHandler.cFirst = splitCard[4]
        dataHandler.cLast = splitCard[5]
        dataHandler.cZip = splitCard[6]
    except Exception as e:
        print("Exception in card lock. Are there any more cards? Are your card formatted properly?")
        print(e)
        os.system('pause')
        sys.exit(1)
    finally:
        print("Card lock released")
        cardLock.release()
        if (goMain == True):
            main(True)


def popCard():
    global cards
    print("popCard called")
    if len(cards) == 0:
        print("There are no more cards left!")
        os.system('pause')
        sys.exit(1)
    try:
        cardLock.acquire()
        print("cardLock acquired")
        # global proxies  # i think this was the error
        cards.pop(0)
    except Exception as e:
        print("There was an error while popping cards!")
        print(e)
        cardLock.release()
    finally:
        cardLock.release()
        print("cardLock released")
        main()


def goodCard():
    shell("input tap 94 530")  # No auto tip
    sleep(1)
    shell("input tap 394 426")  # No auto tip again
    sleep(1)
    shell("input tap 490 34")  # Close the screen
    sleep(10)
    # Come back (this is so the balance refreshes properly)
    shell("input tap 434 854")
    sleep(2)
    shell("input tap 434 854")
    sleep(2)
    shell("screencap -p /sdcard/card.png")
    dataHandler.device.pull(
        "/sdcard/card.png", "./res\\{}.png".format(dataHandler.email))
    sleep(5)
    main()


def readXml():
    try:
        with open("./tmp/{}.xml".format(dataHandler.device.serial), "r") as the_file:
            dataHandler.xml = the_file.read()
            print("XML has been read!")
            print(dataHandler.xml)
            # if "The card number is invalid" in dataHandler.xml:
            #     print("Invalid card number!")
            #     getCard()
            # elif 'text="Error"' in dataHandler.xml:
            #     print("Error (likely declined?)")
            #     getCard()
            # elif 'Success!' or 'has been loaded onto your Dutch Pass' in dataHandler.xml:
            #     goodCard()
            # else:
            #     print("Why did we reach here?")
    except Exception as e:
        print("An error has occurred while opening the XML!")
        print(e)
        os.system('pause')
        sys.exit(1)
    # Next func!
    if "The card number is invalid" in dataHandler.xml:
        print("Invalid card number!")
        getCard(True)
    elif 'text="Error"' in dataHandler.xml:
        print("Error (likely declined?)")
        getCard(True)
    elif 'Success!' or 'has been loaded onto your Dutch Pass' in dataHandler.xml:
        goodCard()
    else:
        print("Why did we reach here?")


def dumpXml():
    shell('uiautomator dump')
    dataHandler.device.pull(
        "/sdcard/window_dump.xml", "{}\\tmp\\{}.xml".format(sys.path[0], dataHandler.device.serial))
    readXml()


def deviceHandler():
    print('Device handler goes here')
    global threads
    for instance in devices:
        threads.insert(devices.index(instance),
                       threading.Thread(target=setDevice, args=[devices.index(instance)]))
        threads[devices.index(instance)].start()


# This is a client for adb, it needs to be started before we connect.
def startClient():
    global adb
    global devices
    subprocess.check_call(["./platform-tools/adb.exe", "start-server"])
    sleep(2)
    adb = Client(host='127.0.0.1', port=5037)
    devices = adb.devices()  # This lists the devices in an array.
    # Check if there are any devices so we don't have an error.
    if len(devices) == 0:
        print('No devices are attached!')
        os.system('pause')
        sys.exit(1)
    else:
        global threaded
        threaded = True
        print(devices)
        deviceHandler()


# We'll use this function so that we can send shell commands with a sleep afterwards to avoid any complications.
def shell(string, period=0.05):
    if threaded == False:
        device.shell(string)
    else:
        dataHandler.device.shell(string)
    sleep(period)


def loadCards():
    try:
        global cards
        cards = []
        with open("./cards.txt", "r") as the_file:
            cards = the_file.readlines()
            print("Cards loaded! Total cards: {}".format(len(cards)))
    except:
        print("An error has occurred while opening cards.txt. Please check that cards.txt is created and contains valid cards.")
        os.system('pause')
        sys.exit(1)
    startClient()


def loadAccounts():
    try:
        global accounts
        accounts = []
        with open("./accounts.txt", "r") as the_file:
            accounts = the_file.readlines()
            print("Accounts loaded! Total accounts: {}".format(len(accounts)))
    except:
        print("An error has occurred while opening accounts.txt. Please check that accounts.txt is created and contains valid accounts.")
        os.system('pause')
        sys.exit(1)
    loadCards()


def start():
    # We need to be in the directory of the script for token.txt
    os.chdir(sys.path[0])
    sys.setrecursionlimit(10**6)
    # Get to the first process! This can be startClient(), but sometimes may need to be altered.
    # In this example, we do not use loadProxies(), so if that functionality is needed, the order should be altered.
    loadAccounts()


def postMain():
    sleep(1)
    shell("input tap 550 540")  # Skip first thing
    sleep(0.5)
    shell("input tap 550 540")  # Skip second thing
    shell("input tap 450 900")  # Open payment menu
    shell("input tap 250 500")  # Charge up
    shell("input tap 250 250")  # Open payment methods
    shell("input tap 250 250")  # Add new credit card
    shell("input keyevent KEYCODE_MOVE_END")
    for firstd in range(10):  # TODO: Why is this so slow????
        shell("input keyevent KEYCODE_DEL")
    shell('input text "{}"'.format(dataHandler.cFirst))
    shell("input tap 400 150")
    shell("input keyevent KEYCODE_MOVE_END")
    for lastd in range(15):  # TODO: This too!
        shell("input keyevent KEYCODE_DEL")
    shell('input text "{}"'.format(dataHandler.cLast))
    shell("input keyevent 66")
    shell("input text {}".format(dataHandler.cNum))
    shell("input keyevent 66")
    shell("input text {}".format(dataHandler.cCvv))
    shell("input keyevent 66")
    shell("input text {}".format(dataHandler.cMonth))
    shell("input keyevent 66")
    shell("input text {}".format(dataHandler.cYear))
    shell("input keyevent 66")
    shell("input text {}".format(dataHandler.cZip))
    shell("input tap 50 350")
    shell("input tap 450 500")
    shell("input tap 250 650")
    shell("input tap 50 900")
    sleep(2)
    dumpXml()


def main(noReg=False):
    shell("pm clear com.dutchbros.loyalty")
    sleep(1)
    shell("monkey -p com.dutchbros.loyalty -c android.intent.category.LAUNCHER 1")
    if noReg == False:
        try:
            print("Register lock acquired")
            regLock.acquire()
            currentAccount = accounts[0]
            accounts.pop(0)
            splitAccount = currentAccount.split(':')
            dataHandler.email = splitAccount[0]
            dataHandler.password = splitAccount[1]
        except Exception as e:
            print("Exception in register lock")
            print(e)
        finally:
            print("Register lock released")
            regLock.release()
    if hasattr(dataHandler, 'cNum') == False:
        getCard()
    sleep(10)
    shell("input tap 300 850", 0.5)  # to skip the thingy
    shell("input tap 250 570")  # This presses "Create an account"
    shell("input text {}@yopmail.com".format(dataHandler.email))  # Email goes here
    shell("input keyevent 66")
    shell("input text {}".format(dataHandler.password))  # Password goes here
    shell("input tap 50 900")  # Log in!
    postMain()


start()
