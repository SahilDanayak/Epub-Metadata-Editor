import tkinter as tk
from ebooklib import epub
from src.styles import *
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from io import BytesIO
import warnings
from src.metadata import MetadataWindow

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

class HomePage(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EPUB Metadata Viewer")
        self.geometry("800x600")
        self.configure(bg=color_palette['primary'])
        self.current_epub_path = None
        self.create_widgets()

    def create_widgets(self):
        # Main container
        main_frame = tk.Frame(self, bg=color_palette['primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        self.left_frame = tk.Frame(main_frame, bg=color_palette['primary'])
        self.left_frame.place(relx=0, rely=0, relwidth=0.4, relheight=1)

        middle_frame = GradientFrame(main_frame, color1=color_palette['primary'], color2='white')
        middle_frame.place(relx=0.4, rely=0, relwidth=0.1, relheight=1)

        self.right_frame = tk.Frame(main_frame, bg='white')
        self.right_frame.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)

        open_button = tk.Button(self.left_frame, text="Open EPUB", **button_style, command=self.open_epub)
        open_button.pack(pady=(50,20))

        self.cover_label = tk.Label(self.left_frame, text="Cover Image",**cover_style)
        self.cover_label.pack(padx=50, pady=10)

        upload_button = tk.Button(self.left_frame, text="Import Metadata", **button_style, command=self.import_metadata)
        upload_button.pack(pady=10)

        save_button = tk.Button(self.left_frame, text="Save EPUB", **button_style, command=self.save_epub)
        save_button.pack(pady=10)

        #Right Panel

        # Title field
        self.title_entry = tk.Entry(self.right_frame, width=50, **title_style)
        self.title_entry.pack(fill=tk.X, padx=10, pady=(30,20))

        # Author field
        self.author_entry = tk.Entry(self.right_frame, width=50, **author_style)
        self.author_entry.pack(fill=tk.X, padx=10, pady=(0,20))

        # Description field
        self.description_label = tk.Label(self.right_frame, text="", **label_style)
        self.description_label.pack(anchor='w')
        self.description_text = tk.Text(self.right_frame, height=10, width=50, **description_style)
        self.description_text.pack(fill=tk.BOTH, padx=10, expand=True)

    def import_metadata(self):
        MetadataWindow(self)

    def open_epub(self):
        file_path = filedialog.askopenfilename(
            initialdir=r"C:\Users\sahil\Downloads\Novels",
            filetypes=[("EPUB files", "*.epub")]
        )
        if not file_path:
            print("No file selected. Exiting.")
            return

        try:
            book = epub.read_epub(file_path, options={'ignore_ncx': True})
            self.current_epub_path = file_path

            # Extract metadata
            title = book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else "Unknown"
            author = book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else "Unknown"
            description = book.get_metadata('DC', 'description')[0][0] if book.get_metadata('DC', 'description') else "No description available"

            # Extract cover image
            cover_image = None
            for item in book.items:
                if "image" in item.media_type and "cover" in item.file_name.lower():
                    cover_image = Image.open(BytesIO(item.get_content()))
                    break

            self.display_details(title, author, description, file_path, cover_image)

        except KeyError as e:
            messagebox.showerror("Error", f"Missing file in EPUB: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read EPUB file: {e}")

    def display_details(self,title, author, description, file_path, cover_image):
        # Insert details into editable text boxes
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, title)

        self.author_entry.delete(0, tk.END)
        self.author_entry.insert(0, author)

        self.description_text.delete("1.0", tk.END)
        self.description_text.insert(tk.END, description)

        self.description_label.config(text="SYNOPSIS:")

        # file_path_label.config(text=f"File Path: {file_path}")

        # Display cover image
        if cover_image:
            cover_image = cover_image.resize((200,300))
            cover_photo = ImageTk.PhotoImage(cover_image)
            self.cover_label.config(image=cover_photo, text="", relief=tk.FLAT, width=200, height=300)
            self.cover_label.image = cover_photo
        else:
            self.cover_label.config(image="", text="No Cover Image Available", **cover_style)
    
    def get_metadata_from_gui(self):
        metadata = {}
        
        metadata['title'] = self.title_entry.get().strip() or "No Title"
        metadata['author'] = self.author_entry.get().strip() or "Unknown Author"
        metadata['description'] = self.description_text.get("1.0", tk.END).strip() or "No description available"
        metadata['cover'] = None
        if hasattr(self.cover_label, 'image'):
            metadata['cover'] = self.cover_label.image
            
        return metadata

    def save_epub(self):
            metadata = self.get_metadata_from_gui()
            file_path = filedialog.asksaveasfilename( defaultextension=".epub", filetypes=[("EPUB files", "*.epub")], initialfile=metadata['title'] )
            print(file_path)
            
            if not file_path:
                print("Couldnt get a valid file path")
                return
                
            # Load original epub
            book = epub.read_epub(self.current_epub_path,options={'ignore_ncx': True, 'ignore_missing_css': True})
            # Update metadata
            book.metadata['http://purl.org/dc/elements/1.1/']['title'] = [(metadata['title'], {})]
            book.metadata['http://purl.org/dc/elements/1.1/']['creator'] = [(metadata['author'], {})]
            book.metadata['http://purl.org/dc/elements/1.1/']['description'] = [(metadata['description'], {})]
            
            for item in book.get_items():
                if 'cover' in item.get_name().lower():
                    book.items.remove(item)
            
            # Update cover if changed
            if metadata['cover']:
                selected_image = ImageTk.getimage( metadata['cover'] ).convert('RGB')
                cover_image_bytes = BytesIO()
                selected_image.save(cover_image_bytes, format="JPEG")
                book.set_cover(content=cover_image_bytes.getvalue(), file_name='cover.jpg')
            
            # Save modified epub
            epub.write_epub(file_path, book)
            messagebox.showinfo("Success", "EPUB file saved successfully!")     
