import cv2
from prettytable import PrettyTable
import speech_recognition as sr
from gtts import gTTS
import os
import pygame
import time
from product import product_db

def speak(text):
    print(f"Speaking: {text}")
    tts = gTTS(text=text, lang='en')
    tts.save("output.mp3")
    
    pygame.mixer.init()
    pygame.mixer.music.load("output.mp3")
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():
        time.sleep(0.5)
    
    pygame.mixer.music.unload()
    os.remove("output.mp3")

# Cart to hold items
cart = []

def scan_qr_code(frame):
    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(frame)
    
    if bbox is not None:
        print("QR Code detected")
        if data:
            prod = product_db.get(data)
            return prod
        else:
            print("No data found in QR Code")
    else:
        print("No QR Code detected")
    
    return None

def add_to_cart(product):
    """
    Adds a product to the cart.
    """
    global cart  # Declare that we're using the global cart variable
    cart.append(product)
    command = f"Added {product['name']} to cart. Price: Rs.{product['price']:.2f}"
    print(command)
    speak(command)

def display_cart():
    if not cart:
        print("Your cart is empty.")
        return 0, "", ""
    
    table = PrettyTable()
    table.field_names = ["No.", "Product Name", "Price"]
    
    total_price = 0
    for idx, item in enumerate(cart, start=1):
        table.add_row([idx, item['name'], f"Rs.{item['price']:.2f}"])
        total_price += item['price']
    
    print("\nCart Summary:")
    print(table)
    
    total = f"\nYour total is: Rs.{total_price:.2f}\n"
    speak(total)

    try:
        with open("purchase.txt", "w") as f:
            f.write("Cart Summary:\n")
            f.write(str(table) + "\n")
            f.write(total + "\n")
    except Exception as e:
        print(f"Error writing to purchase.txt: {e}")
    
    return total_price, str(table), total

def process_payment(payment_option, total_price):
    if payment_option == '1':
        print("Processing Credit Card Payment...")
        card_number = input("Enter your credit card number: ").strip()
        card_expiry = input("Enter card expiry date (MM/YY): ").strip()
        card_cvc = input("Enter card CVC: ").strip()
        print(f"Processing payment of Rs.{total_price:.2f}...")
        return "Payment successful! Thank you for using your credit card."
    
    elif payment_option == '2':
        print("Processing Debit Card Payment...")
        card_number = input("Enter your debit card number: ").strip()
        card_expiry = input("Enter card expiry date (MM/YY): ").strip()
        card_cvc = input("Enter card CVC: ").strip()
        print(f"Processing payment of Rs.{total_price:.2f}...")
        return "Payment successful! Thank you for using your debit card."
    
    elif payment_option == '3':
        print("Processing Cash Payment...")
        amount_paid = float(input("Enter the amount you are paying with: Rs.").strip())
        change = amount_paid - total_price
        print(f"Payment successful! Your change is: Rs.{change:.2f}")
        return f"Payment successful! Your change is: Rs.{change:.2f}"
    
    else:
        print("Invalid payment option selected.")
        return "Invalid payment option selected."
    
def write_receipt_to_file(name,table_str, total, payment_message):
    """
    Writes the cart summary, total, and payment message to a file.
    """
    try:
        file_path = "purchase.txt"
        print("Saving receipt to:", os.path.abspath(file_path))
        
        with open(file_path, "w") as f:
            f.write("Walmart Go:\n")
            f.write(f"Name :{name}\n")
            f.write("Cart Summary:\n")
            f.write(table_str + "\n")
            f.write(total + "\n")
            f.write(payment_message + "\n")
        print("Receipt written to purchase.txt")
    except Exception as e:
        print(f"Error writing to purchase.txt: {e}")


def main():
    # Initial greeting
    speak("Hello! Welcome to Walmart Go.")
    
    # Ask for the user's name
    speak("What is your name?")
    
    # Recognize speech input for the user's name
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source, timeout=5, phrase_time_limit=5)
    
    try:
        name = r.recognize_google(audio)
        speak(f"Hello, {name}! Let's start shopping!")
    except sr.UnknownValueError:
        speak("Sorry, I didn't catch that. Let's call you Shopper. Let's start shopping!")
        name = "Shopper"
    except sr.RequestError:
        print("Sorry, I'm having trouble recognizing speech right now.")
        return
    
    # Start shopping
    speak("Please scan your QR code here.")
    cap = cv2.VideoCapture(0)  # Open camera
    
    if not cap.isOpened():
        print("Error: Camera not accessible.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        cv2.imshow("QR Code Scanner", frame)
            
        product = scan_qr_code(frame)
            
        if product:
            add_to_cart(product)
            cv2.waitKey(2000)  # Wait for 2 seconds to prevent multiple reads of the same QR code
            
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    total_price, table_str, total = display_cart()
    
    if total_price > 0:
        speak("Proceeding to payment.")
        print("Payment Options:")
        print("1. Credit Card")
        print("2. Debit Card")
        print("3. Cash")
        
        payment_option = input("Select payment method (1/2/3): ").strip()
        
        if payment_option in ['1', '2', '3']:
            payment_message = process_payment(payment_option, total_price)
            
            # Write the cart summary, total, and payment message to the file
            write_receipt_to_file(name,table_str, total, payment_message)
        else:
            print("Invalid payment option selected.")
    else:
        print("No items in the cart. No payment needed.")

if __name__ == "__main__":
    main()