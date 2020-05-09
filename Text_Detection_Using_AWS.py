# Importing 
import numpy as np
import boto3
import cv2
import csv
import os
import glob
from os import walk
import imutils




# Reading Credentials of AWS Textract

with open('Cred.csv','r') as input:
    next(input)
    reader = csv.reader(input)
    for line in reader :
        access_key_id = line[2]
        secret_access_key = line[3]
        

client = boto3.client('textract',region_name = 'us-west-2',
                      aws_access_key_id = access_key_id,
                      aws_secret_access_key = secret_access_key)





# State code for finding Registration Number

states = ['AR','AS','BR','CG','GA','GJ',
         'HR','HP','JH','KA','KL','MP','MH','MN',
         'ML','MZ','NL','OD','PB','RJ','SK','TN','TS'
         ,'TR','UP','UK','WB','AN','CH','DD','DL','JK']


# To detect the Registration Number

def Reg(s):
    if len(s) == 10 :
        for a in states :
            if a == s[0:2].upper():
                
                return s

#Manufacture Date 
            
def Mfg(s):
    if len(s) == 7 :
            if '/' in s:
                return s
            

# Chassis Number

def Chs(s):
    if len(s) == 17 or len(s) == 16 or len(s) == 15:
        if s[0:2].lower() == "ma":
            return s


#Function To split 
def split(word): 
    return [char for char in word]  

# Function to convert a list to string 

def listToString(s): 
	
	# initialize an empty string 
	str1 = "" 
	
	# traverse in the string 
	for ele in s: 
		str1 += ele 
	
	# return string 
	return str1 
		
		


# Reg Date

def Rdt(s):
    if len(s) == 10:
        if '/' in s :
            s = split(s)
            s[2] = '/'
            s[5] = '/'
            s = listToString(s)
            return s


#######################################################################

#Accessing All Files in Photos


#Getting All Photos name in Test_Data Folder

f = []
for (dirpath, dirnames, filenames) in walk("Test_Data/"):
    f.extend(filenames)
    break

# Creating XLSM file to store Details
# import xlsxwriter module 
import xlsxwriter 
  
# which is the filename that we want to create. 
workbook = xlsxwriter.Workbook('Results_Test_Data.xlsx') 

worksheet = workbook.add_worksheet() 

#Adding First Row containing Labels

worksheet.write('A1', 'Image Name') 
worksheet.write('B1', 'Name') 
worksheet.write('C1', 'Registration Number') 
worksheet.write('D1', 'Registration Date') 
worksheet.write('E1', 'Manufacture Date') 
worksheet.write('F1', 'Chassis Number') 
worksheet.write('G1', 'Engine Number') 

#workbook.close()



####################################################

#Function to remove noise from image

def remove_noise_and_smooth(image):
    img = image
    filtered = cv2.adaptiveThreshold(img.astype(np.uint8), 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 41)
    kernel = np.ones((1, 1), np.uint8)
    opening = cv2.morphologyEx(filtered, cv2.MORPH_OPEN, kernel)
    closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)
    #img = image_smoothening(img)
    or_image = cv2.bitwise_or(img, closing)
    return or_image


# Declaring Variables

name = 'None'
reg = 'None'
rdt = 'None'
mfg = 'None'
chs = 'None'
eng = 'None'


# To count numbers of data read
count = 1

############################################################################################

#Looping over all data sets in Test_Data Folder

for i in f:
    
    # dir has current directory of image
    dir = "Test_Data/{}".format(i)
    
    # reading that image
    image = cv2.imread(dir)
    
    #Using grayscale to converyt image into gray
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    #U Removing noise from the image 
    img = remove_noise_and_smooth(gray)
    img = gray
    
    # Saving image as temp.jpg
    cv2.imwrite("temp.jpg",img)
    
    
    # Opening Image after preprocessing
    
    with open("temp.jpg" , 'rb') as source:
        source_bytes = source.read()
    
    # Sending image to AWS and receiving data
    response = client.detect_document_text(Document = {'Bytes': source_bytes})
    
    #Contains all data
    detect = response['Blocks']
    
    # Flag for Finding Registration Date
    flag = 0
    
    # Flag for Finding Name 
    flag1 = 0
    name =''
    
    #Flag for Engine Number
    flage = 0
    
    #Flag for Chassis Number
    flagc = 0
    
    for b in detect:
        if b['BlockType'] == 'WORD':
            #print("{} {}".format(b['Text'],len(b['Text'])))
            
            #Containing all Texts
            text = b['Text']
            
            # Removing ':' if the text begins with that 
            if text[0]==':' and len(text)!=1:
                text=text[1:]
            
            if (Reg(text)!= None):
                reg = Reg(text)
            
            if (Mfg(text)!= None):
                mfg = Mfg(text)
                
            if (Chs(text)!= None) and flagc == 0:
                chs = Chs(text)
                flagc = 1
            
            #For Finding Engine Number    
            
            if flage == 1 and text.lower()!='no' and text!='I' and text!=':' and len(text)>=6:
                eng = text
                flage=0
            
            
            if text == 'E' or text.upper() == 'ENGINE'   :
                flage = 1
                
                
            #For Finding Name  
            
            if flag1 == 1 and (text != 'I' and text !=':') :
                #print("DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD")
                if text[0].upper() == 'S' and text[-1].upper() == 'D':
                    flag1 = 0
                
                elif len(name) >= 20:
                    flag1 = 0
                
                else :
                    name = name + text +' '
                    
            if 'NAME' in text.upper():
                flag1 = 1
                
            
                
                
                
                
            #For Finding Registration Number   
            ##################################################################
            
            if 'REG' in text.upper() :
                if flag == -1 :
                    pass
                else:
                    flag = 1
            
            if flag == 1 or flag == 2:
                flag = flag + 1
                
            if (Rdt(text)!= None) and (flag == 3 or flag == 2 or flag == 4):
                rdt = Rdt(text)
                #print("                  "+rdt)
                flag = -1
            
            #print("                  "+str(flag))
            
            if flag == 4:
                flag = -1
                
                
                
    print("{}".format(i))        
    print("Name "+ str(name))
    print("Reg Number "+str(reg))
    print("Reg Date "+str(rdt))
    print("Manufacture Date "+str(mfg))
    print("Chassis Number "+str(chs))
    print("Engine Number "+str(eng))
    print(" ")
    
 
    
    
    #Incrementing Value
    count = count + 1
    
    #Saving Details in the excel sheet
    worksheet.write('A{}'.format(count), str(i) )
    worksheet.write('B{}'.format(count), name) 
    worksheet.write('C{}'.format(count), reg) 
    worksheet.write('D{}'.format(count), rdt) 
    worksheet.write('E{}'.format(count), mfg) 
    worksheet.write('F{}'.format(count), chs) 
    worksheet.write('G{}'.format(count), eng)  
    
    #Resetting values
    name = 'None'
    reg = 'None'
    rdt = 'None'
    mfg = 'None'
    chs = 'None'
    eng = 'None'
    
    
    
#Closing Excel File 
workbook.close()
