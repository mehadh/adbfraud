import os
from ppadb.client import Client  # What we use to connect to the Android shell
from time import sleep  # For waiting
import requests  # Integrating yopmail
from bs4 import BeautifulSoup  # Parsing yopmail!
import cloudscraper  # Cloudflare bypass?
from imagetyperzapi3 import imagetyperzapi
import os  # file system
import sys  # file system
import threading
import subprocess

adb = None
devices = None
device = None
ita = None
proxies = []
number = None
email = None
emailCounter = 0
threads = []
threaded = True
dataHandler = threading.local()
proxyLock = threading.Lock()
regLock = threading.Lock()


def setDevice(num):
    dataHandler.device = devices[num]
    register()


def deviceHandler():  # Need to make this work with multiple instances
    print('Device handler goes here')
    #global device
    #device = devices[0]
    global threads
    # register()
    for instance in devices:
        threads.insert(devices.index(instance),
                       threading.Thread(target=setDevice, args=[devices.index(instance)]))
        #dataHandler = threading.local()
        #dataHandler.device = instance
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
        quit()
    # elif len(devices) == 1:
    #    global device
    #    device = devices[0]
    #    register()
    else:
        global threaded
        threaded = True
        print(devices)
        deviceHandler()


# assumption that first device is who we want to bind to, this has to be altered later to work with multiple clients
#device = devices[0]


# We'll use this function so that we can send shell commands with a sleep afterwards to avoid any complications.
def shell(string, period=0.5):  # usually 0.05 adjusting for fun rn
    if threaded == False:
        device.shell(string)
    else:
        dataHandler.device.shell(string)
    sleep(period)


def register():
    shell("pm clear com.dutchbros.loyalty")
    global number
    global email
    global emailCounter
    try:
        print("Register lock acquired")
        regLock.acquire()
        number += 1
        emailCounter += 1
        dataHandler.number = number
        dataHandler.emailCounter = emailCounter
    except Exception as e:
        print("Exception in register lock")
        print(e)
    finally:
        print("Register lock released")
        regLock.release()
    #number += 1
    #emailCounter += 1
    # This command launches the app
    shell("monkey -p com.dutchbros.loyalty -c android.intent.category.LAUNCHER 1", 5)
    sleep(5)
    shell("input tap 300 850", 0.5)  # to skip the thingy
    shell("input tap 250 540")  # This presses "Create an account"
    sleep(1)
    shell("input text dustin")  # Input the first name
    shell("input keyevent 66")  # This keyevent is to press enter
    shell("input text leveridge")  # Last name
    shell("input keyevent 66")
    shell("input keyevent 66")
    shell("input tap 250 540")  # Set one day ahead.
    # Swipe up so we get a random year that is old enough.
    shell("input swipe 320 540 9999 9999 100")
    shell("input tap 450 600")  # Confirm the DOB.
    shell("input tap 450 350")  # Now we have to click the next field.
    # Enter the phone number edit: This has to change every time!
    #shell("input text {}".format(number))
    shell("input text {}".format(dataHandler.number))
    shell("input keyevent 66")
    shell("input text 02151")  # Zip code
    shell("input keyevent 66")
    # shell("input text {}{}@yopmail.com".format(email, emailCounter))  # Email
    shell("input text {}{}@yopmail.com".format(email, dataHandler.emailCounter))
    shell("input keyevent 66")
    # shell("input text {}{}@yopmail.com".format(email, emailCounter))  # Confirm email
    shell("input text {}{}@yopmail.com".format(email, dataHandler.emailCounter))
    shell("input keyevent 66")
    shell("input text Password777!")  # Password
    shell("input keyevent 66")
    shell("input text Password777!")  # Confirm password
    shell("input tap 50 760")  # Unsubscribe from emails
    shell("input tap 50 850")  # Agree to the terms
    shell("input tap 50 900")  # Signup!
    sleep(6)
    #fetchMail("{}{}@yopmail.com".format(email, emailCounter))
    fetchMail("{}{}@yopmail.com".format(email, dataHandler.emailCounter))


# This would be the end of the initial sign up process. If we want to continue after this, we have three options.
# Option one is to have some sort of API or other way of knowing when the verification is done, perhaps even automatically verifying the account.
# Option two is wait for user input to tell us when the verification is done.
# Option three is to end the script here.


# register()

# Note: yp, yj, ycons, yses, all might need replacing at some point.

headers = {  # Turns out we don't need anything other than the cookie, and at that, we don't need all the info in the cookie, just the ycons, yses(sion?), and ytime (even if ytime is outdated)
    'Cookie': 'ycons=6zrdhP9yeXHqed0gwrfSUqasSu/NHP/ZEl/6WzL2VeM; yses=DdxuZdNlLY0mgiqxFm1QaIuyxHW9RdNqa22h4Syq8dSZceNLyrsNxF3gbSvYav6O; ytime=9:26',
}   # Upon further investigation, we actually do need compte= in order to access an individual email.


def solveCaptcha(url, mail, id):
    try:
        captcha_params = {'page_url': url,
                          'sitekey': '6LcG5v8SAAAAAOdAn2iqMEQTdVyX8t0w9T3cpdN2'}
        captcha_id = ita.submit_recaptcha(captcha_params)
        print("Submitted captcha!")
        response = None
        while not response:
            sleep(10)
            response = ita.retrieve_response(captcha_id)
        answer = response['Response']
        print("Answer received!")
        if mail == "init":
            #fetchMail("{}{}@yopmail.com".format(email, emailCounter), answer)
            fetchMail("{}{}@yopmail.com".format(email,
                      dataHandler.emailCounter), answer)
        else:
            fetchVerify(mail, id, answer)
    except Exception as e:
        print(e)
        print("An error has occurred while submitting the captcha. Starting again.")
        shell("pm clear com.dutchbros.loyalty")
        sleep(1)
        register()


def initCaptcha():
    try:
        tokenfile = open("./token.txt", "r")
    except:
        print("An error has occurred while opening token.txt. Please check that token.txt is created and contains a valid token key.")
        os.system('pause')
        quit()
    access_token = tokenfile.read()
    global ita
    try:
        ita = imagetyperzapi.ImageTyperzAPI(access_token)
        balance = ita.account_balance()
        print("Connected to ImageTyperz successfully! Balance: {}".format(balance))
    except:
        print("An error has occurred while connecting to ImageTyperz. Please check that token.txt is created and contains a valid token key.")
        os.system('pause')
        quit()
    # startClient()  # Proceed to next step
    loadProxies()


def postVerify():
    print("Verification successful.")
    #file = open("{}{}.txt".format(email, emailCounter), "a")
    file = open("{}{}.txt".format(email, dataHandler.emailCounter), "a")
    file.write("Registered.")
    file.close()
    # Probably not necessary if we're gonna stop here.
    shell("input tap 50 900")
    sleep(1)
    shell("pm clear com.dutchbros.loyalty")
    sleep(1)
    register()


def popProxy(verifyLink=None):
    global proxies
    print("popProxy called")
    if len(proxies) == 0:
        print("There are no more proxies left!")
        os.system('pause')
        quit()
    try:
        proxyLock.acquire()
        print("proxyLock acquired")
        # global proxies  # i think this was the error
        proxies.pop(0)
    except Exception as e:
        print("There was an error while popping proxies!")
        print(e)
        proxyLock.release()
    finally:
        proxyLock.release()
        print("proxyLock released")
        if verifyLink != None:
            verify(verifyLink)


def verify(link):
    try:
        proxy = {'http': "http://{}".format(proxies[0])}
        print(proxies[0])
        scraper = cloudscraper.create_scraper()
        response = scraper.get(link, proxies=proxy).text
        # sleep(5) # I don't think this is necessary so let's disable it for now and see what happens.
        # print(response)  # TODO: Check if it actually verifies here
        postVerify()
    except Exception as e:
        print(e)
        print("An error has occurred while clicking the verification link. Retrying with new IP.")
        popProxy(link)


def findLink(link):
    linkStart = str(link[1]).find('href="')
    linkStart += 6
    linkEnd = str(link[1]).find('"><u>Click')
    verLink = str(link[1])[linkStart:linkEnd]
    print("The link: "+verLink)
    verify(verLink)


def fetchVerify(mail, id, captcha="none"):
    if captcha == "none":
        url = "https://yopmail.com/en/mail?b={}&id=m{}".format(mail, id)
    else:
        url = "https://yopmail.com/en/mail?b={}&id=m{}&r_c={}".format(
            mail, id, captcha)
    # print(url)
    newCookie = headers["Cookie"] + str('; compte={}'.format(mail))
    newHeaders = {'Cookie': newCookie}
    proxy = {'http': "http://{}".format(proxies[0])}
    print(proxies[0])
    response = requests.get(url, headers=newHeaders, proxies=proxy)
    if response.status_code == 200:
        print("Accessed verification email!")
        soup = BeautifulSoup(response.text, 'html.parser')
        link = soup.findAll("a")
        if link == []:
            #print("Captcha detected! Consider changing IP address to avoid this.")
            print("Captcha detected! The captcha will be solved.")
            solveCaptcha(url, mail, id)
            # popProxy()
        else:
            findLink(link)

    else:
        print("There was an error in requesting the verification message!")
        print(response)
        print(response.headers)
        print(response.text)


def fetchMail(mail, captcha="none"):
    yp = "DAQL0AwV0ZwD2BGD1AmHjAj"
    yj = "TZmR1AQL2AwpkBGVlAQRkAj"
    if captcha == "none":
        url = "https://yopmail.com/en/inbox?login={}&p=1&d=&ctrl=&yp={}&yj={}&v=5.0&r_c=&id=".format(
            mail, yp, yj)
    else:
        url = "https://yopmail.com/en/inbox?login={}&p=1&d=&ctrl=&yp={}&yj={}&v=5.0&r_c={}&id=".format(
            mail, yp, yj, captcha)
    # print(url)
    proxy = {'http': "http://{}".format(proxies[0])}
    print(proxies[0])
    response = requests.get(url, headers=headers, proxies=proxy)
    if response.status_code == 200:  # We were successful!
        print("Accessed mail box!")
        # print(response)
        # Grab the page into the HTML parser
        soup = BeautifulSoup(response.text, 'html.parser')
        # See about removing currentmail from this since apparently it's not always there so it's kinda useless?
        latest = soup.find("div", {"class": "m", "currentmail": ""})
        if str(latest).find("None") != -1:
            print("Mail not found! Outputting result...")
            print(latest)
            print("Let's try submitting a captcha!")
            # popProxy()
            solveCaptcha(url, "init", "0")
        elif str(latest).find("Dutch Bros Coffee") != -1:
            print("Verification email found!")
            idStart = str(latest).find('id="')
            idEnd = str(latest).find('=="')
            idStart += 4
            idEnd += 2
            id = str(latest)[idStart:idEnd]
            # print(id)
            fetchVerify(mail, id)
        else:
            print("Mail found, but it did not contain Dutch Bros! Outputting result...")
            print(latest)
            print("Let's recheck in 5 seconds...")
            sleep(5)
            #fetchMail("{}{}@yopmail.com".format(email, emailCounter))
            fetchMail("{}{}@yopmail.com".format(email,
                      dataHandler.emailCounter))
    else:
        print("There was an error in requesting the inbox!")
        print(response)
        print(response.headers)
        print(response.text)


def loadProxies():
    try:
        global proxies
        proxies = []
        with open("./proxies.txt", "r") as the_file:
            proxies = the_file.readlines()
            print("Proxies loaded! Total proxies: {}".format(len(proxies)))
    except:
        print("An error has occurred while opening proxies.txt. Please check that proxies.txt is created and contains valid proxies.")
        os.system('pause')
        quit()
    startClient()


def promptEmail():
    global email
    word = input("Enter a word: ")
    if word != None or len(word) > 0:
        email = word
        start()


def promptNum():
    global number
    give = input("Enter a 10 digit phone number to start from: ")
    if len(give) != 10 or give.isnumeric() == False:
        print("Not a valid number!")
        promptNum()
    if (give[0] == "1"):
        print("The first digit should not be 1.")
        promptNum()
    else:
        number = int(give)
        promptEmail()


def start():
    # We need to be in the directory of the script for token.txt
    os.chdir(sys.path[0])
    sys.setrecursionlimit(10**6)
    initCaptcha()  # Initialize captcha client and get to work!


promptNum()
