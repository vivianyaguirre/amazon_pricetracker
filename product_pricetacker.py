import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime
import threading
import time

# Function to check the price of a given product URL
def check_price(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Accept-Language': 'en-GB,en;q=0.9',
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    title_element = soup.select_one('#productTitle')
    price_symbol_element = soup.select_one('.a-price-symbol')
    whole_price_element = soup.select_one('.a-price-whole')
    fraction_price_element = soup.select_one('.a-price-fraction')

    if title_element and price_symbol_element and whole_price_element and fraction_price_element:
        title = title_element.text.strip()
        price_symbol = price_symbol_element.text.strip()
        whole_price = whole_price_element.text.strip().replace('.', '')
        fraction_price = fraction_price_element.text.strip()
        price = float(f"{whole_price}.{fraction_price}")
        return title, f"{price_symbol}{price}"
    else:
        return None, None

# Function to save price history to a CSV file
def save_price_to_csv(product_title, product_url, price):
    filename = f"{product_title}_pricetrack.csv"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not os.path.exists(filename):
        with open(filename, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(["Date", "Title", "URL", "Price"])

    with open(filename, 'a', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow([now, product_title, product_url, price])

# Function to load price history from CSV
def load_price_history():
    all_files = [f for f in os.listdir() if f.endswith('_pricetrack.csv')]
    price_history = []

    for file in all_files:
        with open(file, 'r') as csvfile:
            csvreader = csv.reader(csvfile)
            next(csvreader, None)  # Skip the header
            for row in csvreader:
            
                if row:
                    price_history.append(row)
    return price_history

# Periodic price check functionality
def periodic_price_check(url, interval, stop_event):
    while not stop_event.is_set():
        product_title, product_price = check_price(url)
        if product_title and product_price:
            save_price_to_csv(product_title, url, product_price)
        time.sleep(interval)

# GUI Functionality
def add_product():
    url = url_var.get().strip()
    if not url:
        messagebox.showerror("Input Error", "Please enter a valid URL!")
        return

    product_title, product_price = check_price(url)
    if not product_title or not product_price:
        messagebox.showerror("Error", "Failed to fetch product details. Check the URL.")
        return

    # Save to a specific CSV file for the product
    save_price_to_csv(product_title, url, product_price)
    messagebox.showinfo("Success", f"Added {product_title} with price {product_price}!")

    # Ask if the user wants to enable periodic checking
    enable_check = messagebox.askyesno("Periodic Check", "Would you like to check the price habitually?")
    if enable_check:
        interval_choice = simpledialog.askstring("Choose Interval", "How often? (1: daily, 2: weekly, 3: monthly)")
        if interval_choice == "1":
            interval = 86400  # Daily
        elif interval_choice == "2":
            interval = 604800  # Weekly
        elif interval_choice == "3":
            interval = 2592000  # Monthly
        else:
            messagebox.showerror("Input Error", "Invalid choice. Periodic check not enabled.")
            return

        stop_event = threading.Event()
        thread = threading.Thread(target=periodic_price_check, args=(url, interval, stop_event))
        thread.daemon = True
        thread.start()

    # Update tree view
    update_price_history_tree()
    url_var.set("")  # Clear the input box

def update_price_history_tree():
    # Clear existing data
    for row in tree.get_children():
        tree.delete(row)

    # Load price history and display in the tree view
    price_history = load_price_history()
    for entry in price_history:
        tree.insert('', tk.END, values=entry)

# GUI Setup
root = tk.Tk()
root.title('Amazon Multi-Product Price Tracker')
root.geometry("850x550")
root.configure(background='white')

# Amazon-like Header
header_frame = tk.Frame(root, bg="#232F3E", height=60)
header_frame.pack(fill=tk.X)
header_label = tk.Label(header_frame, text="Amazon Multi-Product Price Tracker", bg="#232F3E", fg="white",
                        font=("Helvetica", 16, "bold"))
header_label.pack(pady=10)

# Input Frame
input_frame = tk.Frame(root, bg="white")
input_frame.pack(fill=tk.X, padx=10, pady=10)

url_label = tk.Label(input_frame, text="Amazon Product URL:", bg="white", font=("Helvetica", 12))
url_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

url_var = tk.StringVar()
url_entry = tk.Entry(input_frame, textvariable=url_var, width=60, font=("Helvetica", 12), fg="gray")
url_entry.insert(0, "Insert product link here")

def on_click(event):
    if url_entry.get() == "Insert product link here":
        url_entry.delete(0, tk.END)
        url_entry.config(fg="black")

def on_focusout(event):
    if not url_entry.get():
        url_entry.insert(0, "Insert product link here")
        url_entry.config(fg="gray")

url_entry.bind("<FocusIn>", on_click)
url_entry.bind("<FocusOut>", on_focusout)
url_entry.grid(row=0, column=1, padx=5, pady=5)

add_button = tk.Button(input_frame, text="Add Product", command=add_product, bg="#FF9900", activebackground="#FF9900", fg="black",
                       font=("Helvetica", 12, "bold"))
add_button.grid(row=0, column=2, padx=5, pady=5)

# Price History Section
tree_frame = tk.Frame(root, bg="white")
tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

tree = ttk.Treeview(tree_frame, columns=("Date", "Title", "URL", "Price"), show="headings", height=15)
tree.heading("Date", text="Date")
tree.heading("Title", text="Product Title")
tree.heading("URL", text="Product URL")
tree.heading("Price", text="Price")
tree.column("Date", width=150)
tree.column("Title", width=300)
tree.column("URL", width=200)
tree.column("Price", width=100)
tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

# Scrollbar for the TreeView
scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
tree.configure(yscrollcommand=scrollbar.set)

# Load Price History into TreeView
update_price_history_tree()

# Footer
footer_frame = tk.Frame(root, bg="#232F3E", height=40)
footer_frame.pack(fill=tk.X)
footer_label = tk.Label(footer_frame, text="Developed by Vivian Aguirre", bg="#232F3E", fg="white",
                        font=("Helvetica", 10))
footer_label.pack(pady=5)

root.mainloop()
