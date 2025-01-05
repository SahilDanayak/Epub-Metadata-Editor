import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from ebooklib import epub
from io import BytesIO
import warnings
import requests
from bs4 import BeautifulSoup
import os

# Suppress warnings from ebooklib
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    'Accept-Language': 'en-GB,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Referer': 'https://www.google.com/'
}

#*************************************************************************************************
#Global variables

current_epub_path = None


#*************************************************************************************************
# Styling

color_palette = {
    'primary': '#e6f3ff',  # Light Blue (Lighter)
    'secondary': '#4a90e2',   # Blue
    'accent': '#ADD8E6',  # Yellow
}

button_style = {'bg': color_palette['secondary'], 'fg': 'white', 'pady': 8, 'width': 40}
label_style = {'bg': 'white', 'font': ('Arial', 10), 'fg': color_palette['secondary'], 'padx': 5, 'pady': 5}
entry_style = {'bg': 'white', 'relief': tk.SOLID, 'bd': 1}
description_style = {
    'bg': 'white',
    'relief': 'flat',
    'font': ('Arial', 10),
    'padx': 5,
    'pady': 5,
    'wrap': 'word',
    'highlightthickness': 0,
}
title_style = {
    'font': ('Arial', 12, 'bold'),
    'bg': 'white',
    'relief': 'flat',
    'justify': 'center',
}
author_style = {
    'font': ('Arial', 10),
    'fg': '#666666',
    'bg': 'white',
    'relief': 'flat',
    'justify': 'center'
}

cover_style = {
    'bg': 'white',
    'relief': 'sunken',
    'bd': 1,
    'height': 20,
    'width': 28,
}

#*************************************************************************************************

#Classes

class GradientFrame(tk.Frame):
    def __init__(self, parent, color1='#e6f3ff', color2='white', **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        self._color1 = color1
        self._color2 = color2
        self.bind('<Configure>', self._draw_gradient)
        
    def _draw_gradient(self, event=None):
        self.canvas.delete("gradient")
        width = self.winfo_width()
        height = self.winfo_height()
        
        limit = width
        (r1,g1,b1) = self.winfo_rgb(self._color1)
        (r2,g2,b2) = self.winfo_rgb(self._color2)
        r_ratio = float(r2-r1) / limit
        g_ratio = float(g2-g1) / limit
        b_ratio = float(b2-b1) / limit

        for i in range(limit):
            nr = int(r1 + (r_ratio * i))
            ng = int(g1 + (g_ratio * i))
            nb = int(b1 + (b_ratio * i))
            color = "#%4.4x%4.4x%4.4x" % (nr,ng,nb)
            self.canvas.create_line(i,0,i,height, tags=("gradient",), fill=color)

#*************************************************************************************************

#Functions

def open_epub():
    global current_epub_path
    file_path = filedialog.askopenfilename(
        initialdir=r"C:\Users\sahil\Downloads\Novels",
        filetypes=[("EPUB files", "*.epub")]
    )
    if not file_path:
        print("No file selected. Exiting.")
        return

    try:
        book = epub.read_epub(file_path, options={'ignore_ncx': True})
        current_epub_path = file_path

        # Extract metadata
        title = book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else "Unknown"
        author = book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else "Unknown"
        description = book.get_metadata('DC', 'description')[0][0] if book.get_metadata('DC', 'description') else "No description available"

        # Extract cover image
        cover_image = None
        # print(title)
        for item in book.items:
            # print(item.file_name, item.media_type)
            # print(item.get_type(),ITEM_IMAGE, "cover" in item.file_name.lower())
            if "image" in item.media_type and "cover" in item.file_name.lower():
                cover_image = Image.open(BytesIO(item.get_content()))
                break

        display_details(title, author, description, file_path, cover_image)

    except KeyError as e:
        messagebox.showerror("Error", f"Missing file in EPUB: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read EPUB file: {e}")

def display_details(title, author, description, file_path, cover_image):
    # Insert details into editable text boxes
    title_entry.delete(0, tk.END)
    title_entry.insert(0, title)

    author_entry.delete(0, tk.END)
    author_entry.insert(0, author)

    description_text.delete("1.0", tk.END)
    description_text.insert(tk.END, description)

    description_label.config(text="SYNOPSIS:")

    # file_path_label.config(text=f"File Path: {file_path}")

    # Display cover image
    if cover_image:
        # cover_image.thumbnail((200, 300)) 
        cover_image = cover_image.resize((200,300))
        cover_photo = ImageTk.PhotoImage(cover_image)
        cover_label.config(image=cover_photo, text="", relief=tk.FLAT, width=200, height=300)
        cover_label.image = cover_photo
    else:
        cover_label.config(image="", text="No Cover Image Available", **cover_style)
 
def get_metadata_from_gui():
    metadata = {}
    
    # Get title
    metadata['title'] = title_entry.get().strip() or "No Title"
    
    # Get author
    metadata['author'] = author_entry.get().strip() or "Unknown Author"

    # Get description
    metadata['description'] = description_text.get("1.0", tk.END).strip() or "No description available"
    
    # Get cover image
    metadata['cover'] = None
    if hasattr(cover_label, 'image'):
        metadata['cover'] = cover_label.image
        
    return metadata

def save_epub():
        metadata = get_metadata_from_gui()
        file_path = filedialog.asksaveasfilename( defaultextension=".epub", filetypes=[("EPUB files", "*.epub")], initialfile=metadata['title'] )
        print(file_path)
        
        if not file_path:
            print("Couldnt get a valid file path")
            return
            
        # Load original epub
        book = epub.read_epub(current_epub_path,options={'ignore_ncx': True, 'ignore_missing_css': True})
        # Update metadata
        book.metadata['http://purl.org/dc/elements/1.1/']['title'] = [(metadata['title'], {})]
        book.metadata['http://purl.org/dc/elements/1.1/']['creator'] = [(metadata['author'], {})]
        book.metadata['http://purl.org/dc/elements/1.1/']['description'] = [(metadata['description'], {})]
        
        # Update cover if changed
        if metadata['cover']:
            selected_image = ImageTk.getimage( metadata['cover'] ).convert('RGB')
            cover_image_bytes = BytesIO()
            selected_image.save(cover_image_bytes, format="JPEG")
            for item in book.get_items():
                if "image" in item.media_type:
                    if 'cover' in item.get_name().lower():
                        book.items.remove(item)
                        break
            
            book.set_cover(content=cover_image_bytes.getvalue(), file_name='cover.jpg')
        
        # Save modified epub
        epub.write_epub(file_path, book)
        messagebox.showinfo("Success", "EPUB file saved successfully!")     

def import_metadata():
    global current_epub_path
    domains = []
    google_books = []; amazon_books = []

    def bind_recursive(parent, canvas):
        parent.bind('<MouseWheel>', lambda e: _on_mousewheel(e, canvas))
        for child in parent.winfo_children():
            bind_recursive(child, canvas)

    def update_book_selection_info(selected_book=None):
        if not selected_book:
            book_details = {
                'title': 'No Book Selected',
                'author': 'Unknown Author',
                'description': 'Please hover a book and select it to continue.'
            }
        else:
            # lazy loading for amazon books
            if selected_book.get('product_url') and not selected_book.get('description'):
                description = fetch_metadata_from_amazon_url(selected_book['product_url'])['description']
                for i in range(len(amazon_books)):
                    if amazon_books[i]['product_url'] == selected_book['product_url']:
                        amazon_books[i]['description'] = description
                        break

            book_details = {
                'title': selected_book['title'],
                'author': selected_book['author'],
                'description': selected_book['description']
            }

        title_field.configure(state=tk.NORMAL)
        title_field.tag_configure('bold', font=('Arial', 10, 'bold'))
        title_field.insert('1.0', book_details['title'], 'bold')
        title_field.insert(tk.END, f", by {book_details['author']}")
        title_field.configure(state=tk.DISABLED)
        description_field.config(text=book_details['description'][:770] + ('...' if len(book_details['description']) > 770 else ''))
        
    def _on_mousewheel(event, canvas):
            # Scroll -120 units on Windows per wheel notch
        canvas.xview_scroll(int(-1 * (event.delta/120)), "units")

    def create_book_card(book, parent):
        
        def on_hover_enter(event):
            title_field.configure(state=tk.NORMAL)
            title_field.delete('1.0', tk.END)
            title_field.configure(state=tk.DISABLED)
            description_field.config(text="Loading..")
            # Reset all cards
            for ele in domains:
                for child in ele.winfo_children():
                    child.configure(bg=color_palette['primary'])
                    for widget in child.winfo_children():
                        widget.configure(bg=color_palette['primary'])
            
            # Highlight hovered card
            card.configure(bg=color_palette['accent'])
            for widget in card.winfo_children():
                widget.configure(bg=color_palette['accent'])
            card.update_idletasks()
            update_book_selection_info(book)
        
        def on_hover_leave(event):
            card.configure(bg=color_palette['primary'])
            for widget in card.winfo_children():
                widget.configure(bg=color_palette['primary'])

        def on_card_click():
            if book:
                # Update cover if available
                cover_image = None
                if book.get('cover_image_url'):
                    response = requests.get(book['cover_image_url'])
                    if response.status_code == 200:
                        cover_image = Image.open(BytesIO(response.content))
                
                display_details(
                    book['title'],
                    book['author'],
                    book['description'],
                    current_epub_path,
                    cover_image
                )
                selection_window.destroy()
                
        card = tk.Frame(parent, width=80, height=170, relief='solid', bg=color_palette['primary'])
        card.pack_propagate(False)
        card.pack(side=tk.LEFT, padx=10, pady=10)
        domains.append(parent)

        # Cover image
        if book.get('cover_image_url'):
            try:
                response = requests.get(book['cover_image_url'])
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content))
                    img = img.resize((80,100))
                    photo = ImageTk.PhotoImage(img)
                    cover = tk.Label(card, image=photo)
                    cover.image = photo
                    cover.pack(pady=5)
            except:
                tk.Label(card, text="No Image", height=10).pack(pady=5)
        
        # Title and Author
        title = book['title'][:25] + ('...' if len(book['title']) > 25 else '')        
        tk.Label(card, text=title, wraplength=80, font=('Arial', 10, 'bold'), justify='center', bg=color_palette['primary']).pack(pady=(0,2))

        card.bind('<Enter>', on_hover_enter)
        card.bind('<Leave>', on_hover_leave)
        for widget in card.winfo_children():
            widget.bind('<Enter>', on_hover_enter)
            widget.bind('<Leave>', on_hover_leave)    
        
        card.bind('<Button-1>', lambda e: on_card_click())
        for widget in card.winfo_children():
            widget.bind('<Button-1>', lambda e: on_card_click())
        
    
    try:
        if not current_epub_path:
            messagebox.showerror("Error", "Please load an EPUB file first")
            return
            
        # Create query from filename
        query = os.path.basename(current_epub_path)
        query = query.replace('.epub', '').replace('_OceanofPDF.com_', '').replace('_', ' ').strip()
        
        # Create selection window
        selection_window = tk.Toplevel()
        selection_window.title("Import Metadata")
        selection_window.geometry("800x600")
        selection_window.configure(bg=color_palette['primary'])
        
        # Google Books Section (Top)
        google_frame = tk.Frame(selection_window, height=200, bg=color_palette['primary'])
        google_frame.pack(fill='x', expand=False)
        
        tk.Label(google_frame, text="Google Books Results", font=('Arial', 12, 'bold'), bg=color_palette['primary']).pack(pady=5)
                
        google_canvas = tk.Canvas(google_frame, height=180, bg=color_palette['primary'])
        google_scrollbar = tk.Scrollbar(google_frame, orient="horizontal", command=google_canvas.xview, bg=color_palette['primary'],)
        google_container = tk.Frame(google_canvas, bg=color_palette['primary'])
        
        google_canvas.configure(xscrollcommand=google_scrollbar.set)

        # Amazon Books Section (Bottom)
        amazon_frame = tk.Frame(selection_window, height=200, bg=color_palette['primary'])
        amazon_frame.pack(fill='x', expand=False)
        
        tk.Label(amazon_frame, text="Amazon Results", font=('Arial', 12, 'bold'), bg=color_palette['primary']).pack(pady=5)
                
        amazon_canvas = tk.Canvas(amazon_frame, height=180)
        amazon_scrollbar = tk.Scrollbar(amazon_frame, orient="horizontal", command=amazon_canvas.xview, bg=color_palette['primary'])
        amazon_container = tk.Frame(amazon_canvas, bg=color_palette['primary'])
        
        amazon_canvas.configure(xscrollcommand=amazon_scrollbar.set)

        # Author field
        title_field = tk.Text( selection_window, height=1, bg=color_palette['primary'], font=('Arial', 10), relief='flat', state=tk.DISABLED)
        title_field.pack(fill=tk.X, padx=10)

        # Description field
        description_field = tk.Label(selection_window,text='Please hover a book and select it to continue.', wraplength=770, bg=color_palette['primary'], justify='left',font=('Arial', 10))
        description_field.pack(fill=tk.BOTH, padx=10, expand=True)

        # Populate Google Books
        google_books = fetch_metadata_via_google_api(query)
        for book in google_books:
            create_book_card(book, google_container)
        
        # Configure Google scrolling
        bind_recursive(google_frame, google_canvas)
        google_canvas.create_window((0,0), window=google_container, anchor="nw")
        google_container.bind("<Configure>", lambda e: google_canvas.configure(scrollregion=google_canvas.bbox("all")))
        google_canvas.pack(side="top", fill="x", expand=True)
        google_scrollbar.pack(side="bottom", fill="x")

        selection_window.update()

        # Populate Amazon Books    
        amazon_books = fetch_metadata_via_amazon(query)
        for book in amazon_books:
            create_book_card(book, amazon_container)
        
        # Configure Amazon scrolling
        bind_recursive(amazon_frame, amazon_canvas)
        amazon_canvas.create_window((0,0), window=amazon_container, anchor="nw")
        amazon_container.bind("<Configure>", lambda e: amazon_canvas.configure(scrollregion=amazon_canvas.bbox("all")))
        amazon_canvas.pack(side="top", fill="x", expand=True)
        amazon_scrollbar.pack(side="bottom", fill="x")
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to import metadata: {str(e)}")

def fetch_metadata_via_google_api(query,maxResults=10):
    """Fetch metadata and images via Google Books API."""
    api_url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults={maxResults}"
    response = requests.get(api_url,headers=headers)
    if response.status_code == 200:
        data = response.json()
        if "items" in data:
            books = []
            for item in data["items"]:
                volume_info = item["volumeInfo"]
                metadata = {
                    "title": volume_info.get("title", "Unknown Title"),
                    "author": ", ".join(volume_info.get("authors", ["Unknown Author"])),
                    "description": volume_info.get("description", "No description available."),
                    "cover_image_url": volume_info.get("imageLinks", {}).get("thumbnail"),
                }
                books.append(metadata)
            return books
    raise Exception("Books not found or API issue.")

def fetch_metadata_via_amazon(search_query,maxResults=5):
    """
    Fetch metadata of the top results for a search query on Amazon.
    """
    
    # Perform search on Amazon
    base_url = "https://www.amazon.in/s"
    books = []
    for index,params in enumerate([{"k": search_query, "i":"stripbooks"}, {"k": search_query, "i":"digital-text"}]):    #i=digital-text for kindle books, i=stripbooks for paperbacks
        response = requests.get(base_url, headers=headers, params=params)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            search_results = soup.select('.s-result-item')
            for result in search_results:
                title_element = result.select_one('h2 span')
                title = title_element.get_text(strip=True) if title_element else "Unknown Title"
                author_element = result.select_one('.a-color-secondary .a-size-base+ .a-size-base')
                url_element = result.select_one('a')
                image_element = result.select_one('.s-image')

                if (title!="Unknown Title"):
                    books.append({
                        "title": title,
                        "author": author_element.get_text(strip=True).replace("(Author)", "").replace("(author)", "").replace("Author","").strip() if author_element else "Unknown Author",
                        "product_url": f"https://www.amazon.in{url_element['href']}" if url_element else None,
                        "cover_image_url": image_element['src'] if image_element else None
                    })
                    if len(books)+1==(index+1)*maxResults:
                        break
        else:
            raise Exception(f"Failed to fetch search results from Amazon. HTTP Status: {response.status_code}")
            
    return books


def fetch_metadata_from_amazon_url(url):
    """
    Fetch detailed metadata from an Amazon book URL.
    """
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('span', {'id': 'productTitle'})
        author = soup.find('span', {'class': 'author'})
        description_element = soup.select_one('#bookDescription_feature_div')
        if description_element:
            for br in description_element.find_all('br'):
                br.replace_with('\n')
            description = description_element.get_text().replace("Read more", "").strip()
        else:
            description = "No description available."
        image_element = soup.select_one('#landingImage')

        image_url = (
            image_element.attrs.get('data-old-hires') if image_element and image_element.attrs.get('data-old-hires')
            else image_element.attrs.get('src') if image_element and image_element.attrs.get('src')
            else None
        )

        return {
            "title": title.get_text(strip=True) if title else 'Unknown Title',
            "author": author.get_text(strip=True) if author else 'Unknown Author',
            "description": description,
            "cover_image_url": image_url
        }
    else:
        raise Exception(f"Failed to fetch data from Amazon. HTTP Status: {response.status_code}")



#*************************************************************************************************

root = tk.Tk()
root.title("EPUB Metadata Viewer")
root.geometry("800x600")  # Increased window size
root.configure(bg=color_palette['primary'])

# Main container
main_frame = tk.Frame(root, bg=color_palette['primary'])
main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

# Left frame (metadata)
left_frame = tk.Frame(main_frame, bg=color_palette['primary'])
left_frame.place(relx=0, rely=0, relwidth=0.4, relheight=1)

# Middle frame
middle_frame = GradientFrame(main_frame, color1=color_palette['primary'], color2='white')
middle_frame.place(relx=0.4, rely=0, relwidth=0.1, relheight=1)

# Right frame
right_frame = tk.Frame(main_frame, bg='white')
right_frame.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)

# Left Panel
open_button = tk.Button(left_frame, text="Open EPUB", **button_style, command=open_epub)
open_button.pack(pady=(50,20))

cover_label = tk.Label(left_frame, text="Cover Image",**cover_style)
cover_label.pack(padx=50, pady=10)

upload_button = tk.Button(left_frame, text="Import Metadata", **button_style, command=import_metadata)
upload_button.pack(pady=10)

save_button = tk.Button(left_frame, text="Save EPUB", **button_style, command=save_epub)
save_button.pack(pady=10)

#Right Panel

# Title field
title_entry = tk.Entry(right_frame, width=50, **title_style)
title_entry.pack(fill=tk.X, padx=10, pady=(30,20))

# Author field
author_entry = tk.Entry(right_frame, width=50, **author_style)
author_entry.pack(fill=tk.X, padx=10, pady=(0,20))

# Description field
description_label = tk.Label(right_frame, text="", **label_style)
description_label.pack(anchor='w')
description_text = tk.Text(right_frame, height=10, width=50, **description_style)
description_text.pack(fill=tk.BOTH, padx=10, expand=True)

root.mainloop()