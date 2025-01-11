import tkinter as tk
from ebooklib import epub
from utils.metadataExtractor import fetch_metadata, fetch_metadata_from_amazon_url
from src.styles import *
import os
import requests
from PIL import Image, ImageTk
from io import BytesIO
import asyncio
import aiohttp

def bind_recursive(parent, canvas):
    parent.bind('<MouseWheel>', lambda event: canvas.xview_scroll(int(-1 * (event.delta/120)), "units") )
    for child in parent.winfo_children():
        bind_recursive(child, canvas)

class BookCard():
    domains = set()

    def __init__(self, book, parentContainer, parent=None):
        self.parentContainer = parentContainer
        self.parent = parent
        self.book = book
        self.create_widgets()
        # print(book)
    
    def create_widgets(self):
        self.card = tk.Frame(self.parentContainer, width=100, height=150, relief='solid', bg=color_palette['primary'])
        self.card.pack_propagate(False)
        self.card.pack(side=tk.LEFT, padx=(0,0), pady=(5,0))
        BookCard.domains.add(self.parentContainer)

        # Cover image
        if self.book['cover_image']:
            self.cover = tk.Label(self.card, image=self.book['cover_image'], bg=color_palette['primary'])
            self.cover.image = self.book['cover_image']
            self.cover.pack()
        else:
            tk.Label(self.card, text="No Image", height=10).pack(padx=5, pady=5)

        # Title and Author
        # title = self.book['title'][:25] + ('...' if len(self.book['title']) > 25 else '')        
        # tk.Label(self.card, text=title, wraplength=80, font=('Arial', 10, 'bold'), justify='center', bg=color_palette['primary']).pack(pady=(0,2))

        self.card.bind('<Enter>', self.on_hover_enter)
        self.card.bind('<Leave>', self.on_hover_leave)
        for widget in self.card.winfo_children():
            widget.bind('<Enter>', self.on_hover_enter)
            widget.bind('<Leave>', self.on_hover_leave)    
        
        self.card.bind('<Button-1>', lambda e: self.on_card_click())
        for widget in self.card.winfo_children():
            widget.bind('<Button-1>', lambda e: self.on_card_click())
        
    def on_hover_enter(self,event, zoom_factor=1.5):
        self.parent.title_field.configure(state=tk.NORMAL)
        self.parent.title_field.delete('1.0', tk.END)
        self.parent.title_field.configure(state=tk.DISABLED)

        img = ImageTk.getimage( self.book['cover_image'] )
        w, h = img.size
        zoom_w = int(w * zoom_factor)
        zoom_h = int(h * zoom_factor)
        zoomed = img.resize((zoom_w+5, zoom_h+5), Image.LANCZOS)
        # zoomed = zoomed.crop(((zoom_w - int(w)) // 2 , (zoom_h - int(h)) // 2, (zoom_w + int(w)) // 2, (zoom_h + int(h)) // 2))
        
        # Update image
        self.zoomed_image = ImageTk.PhotoImage(zoomed)
        self.cover.configure(image=self.zoomed_image)
        self.card.update_idletasks()
        self.parent.update_book_selection_info(self.book)
        
    def on_hover_leave(self,event):
        self.cover.configure(image=self.book['cover_image'])

    def on_card_click(self):
        if self.book:
            if self.book.get('product_url') and not self.book.get('description'):
                data = fetch_metadata_from_amazon_url(self.book['product_url'])
                self.book['description'] = data['description']

                ## high res cover image
                if data['cover_image_url']!= self.book['cover_image_url']:
                    response = requests.get(data['cover_image_url'])
                    if response.status_code == 200:
                        img = Image.open(BytesIO(response.content))
                        self.book['cover_image'] = ImageTk.PhotoImage(img)
            
            self.parent.parent.display_details(
                self.book['title'],
                self.book['author'],
                self.book['description'],
                self.parent.parent.current_epub_path,
                ImageTk.getimage( self.book['cover_image'] )
            )
            self.parent.destroy()

class MetadataWindow(tk.Toplevel):
    def __init__(self,parent):
        super().__init__()
        self.title("Import Metadata")
        self.geometry("800x600")
        self.configure(bg=color_palette['primary'])
        self.create_widgets()
        self.parent = parent

        if not self.parent.current_epub_path:
            messagebox.showerror("Error", "Please load an EPUB file first")
            return
        
        query = os.path.basename(self.parent.current_epub_path)
        query = query.replace('.epub', '').replace('_OceanofPDF.com_', '').replace('_', ' ').strip()

        self.extractMetadata(query)
        
    def create_widgets(self):

        self.description_field = tk.Label(self,text='Please hover a book and select it to continue.', wraplength=770, bg=color_palette['primary'], justify='center',font=('Arial', 12))
        self.description_field.pack(fill=tk.BOTH, padx=10, pady=10 , expand=True)

        self.google_frame = tk.Frame(self, height=200, bg=color_palette['primary'])
        self.google_frame.pack(fill='x', expand=False)
        
        tk.Label(self.google_frame, text="Google Books Results", font=('Arial', 12, 'bold'), bg=color_palette['primary']).pack(pady=5)
                
        self.google_canvas = tk.Canvas(self.google_frame, height=160, bg=color_palette['primary'])
        self.google_scrollbar = tk.Scrollbar(self.google_frame, orient="horizontal", command=self.google_canvas.xview, bg=color_palette['primary'],)
        self.google_container = tk.Frame(self.google_canvas, bg=color_palette['primary'])
        
        self.google_canvas.configure(xscrollcommand=self.google_scrollbar.set)

        # Amazon Books Section (Bottom)
        self.amazon_frame = tk.Frame(self, height=200, bg=color_palette['primary'])
        self.amazon_frame.pack(fill='x', expand=False)
        
        tk.Label(self.amazon_frame, text="Amazon Results", font=('Arial', 12, 'bold'), bg=color_palette['primary']).pack(pady=5)
                
        self.amazon_canvas = tk.Canvas(self.amazon_frame, height=160)
        self.amazon_scrollbar = tk.Scrollbar(self.amazon_frame, orient="horizontal", command=self.amazon_canvas.xview, bg=color_palette['primary'])
        self.amazon_container = tk.Frame(self.amazon_canvas, bg=color_palette['primary'])
        
        self.amazon_canvas.configure(xscrollcommand=self.amazon_scrollbar.set)

        self.title_field = tk.Text( self, height=1, bg=color_palette['primary'], font=('Arial', 11), relief='flat', state=tk.DISABLED)
        self.title_field.pack(fill=tk.X, padx=10, pady=20)


    async def getImages(self,books):

        async def getImage(book , session=None):
            # books is passed by reference
            book['cover_image'] = None
            response = await session.get(book['cover_image_url'])
            if response.status == 200:
                img = Image.open(BytesIO(await response.read()))
                img = img.resize((80,100))
                photo = ImageTk.PhotoImage(img)
                book['cover_image'] = photo
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for book in books:
                tasks.append(getImage(book, session=session))
            return await asyncio.gather(*tasks, return_exceptions=True)

    def extractMetadata(self,query):
        # Fetch Data Parallely
        google_books, amazon_books = fetch_metadata(query)

        # get book images parallely
        asyncio.run(self.getImages(google_books + amazon_books))


        for book in google_books:
            BookCard(book, self.google_container, self)
        
        # Configure Google scrolling
        bind_recursive(self.google_frame, self.google_canvas)
        self.google_canvas.create_window((0,0), window=self.google_container, anchor="nw")
        self.google_container.bind("<Configure>", lambda e: self.google_canvas.configure(scrollregion=self.google_canvas.bbox("all")))
        self.google_canvas.pack(side="top", fill="x", expand=True)
        self.google_scrollbar.pack(side="bottom", fill="x")

        # Populate Amazon Books    
        for book in amazon_books:
            BookCard(book, self.amazon_container, self)
        
        # Configure Amazon scrolling
        bind_recursive(self.amazon_frame, self.amazon_canvas)
        self.amazon_canvas.create_window((0,0), window=self.amazon_container, anchor="nw")
        self.amazon_container.bind("<Configure>", lambda e: self.amazon_canvas.configure(scrollregion=self.amazon_canvas.bbox("all")))
        self.amazon_canvas.pack(side="top", fill="x", expand=True)
        self.amazon_scrollbar.pack(side="bottom", fill="x")

    def update_book_selection_info(self,selected_book=None):
        if not selected_book:
            book_details = {
                'title': 'No Book Selected',
                'author': 'Unknown Author',
            }
        else:
            book_details = {
                'title': selected_book['title'],
                'author': selected_book['author'],
            }

        self.title_field.configure(state=tk.NORMAL)
        self.title_field.tag_configure('bold', font=('Arial', 11, 'bold'))
        self.title_field.insert('1.0', book_details['title'], 'bold')
        self.title_field.insert(tk.END, f", by {book_details['author']}")
        self.title_field.configure(state=tk.DISABLED)
