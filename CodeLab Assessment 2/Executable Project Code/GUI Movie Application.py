import tkinter as tk
from tkinter import ttk, messagebox
import requests
from PIL import Image, ImageTk
from io import BytesIO
from ttkthemes import ThemedTk

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("MovieFlix")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1a1a1a')
        
        self.favs = []
        self.key = "08699292258339097e825d636b483665"
        self.api = "https://api.themoviedb.org/3"
        self.img_url = "https://image.tmdb.org/t/p/w500"
        
        self.setup_style()
        self.build_ui()
        self.setup_loader()
        
        # First load
        self.load_first()

    def load_first(self):
        try:
            resp = requests.get(f"{self.api}/trending/movie/day", 
                              params=dict(api_key=self.key))
            self.show_movies(resp.json()['results'])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load movies: {str(e)}")

    def setup_loader(self):
        self.load_frame = tk.Frame(self.root, bg='#1a1a1a')
        self.load_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        self.loader = ttk.Progressbar(
            self.load_frame,
            mode='indeterminate',
            length=200
        )
        self.loader.pack(pady=10)
        
        self.load_txt = tk.Label(
            self.load_frame,
            text="Loading...",
            fg='white',
            bg='#1a1a1a',
            font=('Helvetica', 12)
        )
        self.load_txt.pack(pady=5)
        
        self.load_frame.place_forget()

    def show_load(self):
        self.load_frame.place(relx=0.5, rely=0.5, anchor='center')
        self.loader.start(10)
        self.root.update()

    def hide_load(self):
        self.loader.stop()
        self.load_frame.place_forget()
        self.root.update()

    def get_movies(self, endpoint, params=None):
        try:
            self.show_load()
            resp = requests.get(f"{self.api}/{endpoint}", 
                              params=dict(api_key=self.key, **(params or {})))
            self.show_movies(resp.json()['results'])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load movies: {str(e)}")
        finally:
            self.hide_load()

    def setup_style(self):
        style = ttk.Style()
        style.configure('Search.TEntry',
            fieldbackground='#2d2d2d',
            foreground='white',
            padding=10,
            font=('Helvetica', 12)
        )
        style.configure('Cat.TButton',
            background='#2d2d2d',
            foreground='white',
            padding=(15, 8),
            font=('Helvetica', 10, 'bold')
        )
        style.map('Cat.TButton',
            background=[('active', '#3d3d3d')],
            foreground=[('active', '#ffffff')]
        )

    def build_ui(self):
        box = tk.Frame(self.root, bg='#1a1a1a', padx=20, pady=20)
        box.pack(fill='both', expand=True)
        
        self.search_txt = tk.StringVar()
        search = ttk.Entry(box, textvariable=self.search_txt, style='Search.TEntry')
        search.pack(fill='x', pady=(0, 20))
        search.insert(0, "Search movies...")
        search.bind('<Return>', lambda e: self.search())
        search.bind('<FocusIn>', lambda e: self.clear_txt(search))
        
        nav = tk.Frame(box, bg='#1a1a1a')
        nav.pack(fill='x', pady=(0, 20))
        btns = [
            ("Trending", self.get_trending),
            ("Popular", self.get_popular),
            ("Top Rated", self.get_top),
            ("Favorites", lambda: self.show_movies(self.favs))
        ]
        for txt, cmd in btns:
            btn = ttk.Button(nav, text=txt, style='Cat.TButton', command=cmd)
            btn.pack(side='left', padx=5)
        
        self.canvas = tk.Canvas(box, bg='#1a1a1a', highlightthickness=0)
        scroll = ttk.Scrollbar(box, orient='vertical', command=self.canvas.yview)
        self.content = tk.Frame(self.canvas, bg='#1a1a1a')
        
        self.content.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.content, anchor='nw', width=self.canvas.winfo_width())
        self.canvas.configure(yscrollcommand=scroll.set)
        
        self.canvas.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        
        self.canvas.bind_all("<MouseWheel>", self.scroll)
        self.root.bind("<Configure>", self.resize)

    def make_card(self, movie, row, col, is_fav=False):
        card = tk.Frame(self.content, bg='#2d2d2d', width=350, height=600)
        card.grid(row=row, column=col, padx=15, pady=15, sticky='nsew')
        card.grid_propagate(False)
        
        card.bind("<Button-1>", lambda e, m=movie: self.show_details(m))
        
        if movie.get('poster_path'):
            try:
                resp = requests.get(f"{self.img_url}{movie['poster_path']}")
                img = Image.open(BytesIO(resp.content)).resize((300, 450))
                photo = ImageTk.PhotoImage(img)
                poster = tk.Label(card, image=photo, bg='#2d2d2d')
                poster.image = photo
                poster.pack(pady=10)
                poster.bind("<Button-1>", lambda e, m=movie: self.show_details(m))
            except:
                tk.Label(card, text="Image Not Available", fg='white', bg='#2d2d2d').pack(pady=10)
        
        title = tk.Label(card, text=movie.get('title', 'Unknown'), fg='white', bg='#2d2d2d',
                        wraplength=300, font=('Helvetica', 12, 'bold'))
        title.pack()
        
        if is_fav:
            ttk.Button(card, text="♥ Remove from Favorites", style='Cat.TButton',
                      command=lambda: self.rm_fav(movie)).pack(pady=5)
        else:
            ttk.Button(card, text="♥ Add to Favorites", style='Cat.TButton',
                      command=lambda: self.add_fav(movie)).pack(pady=5)

    def rm_fav(self, movie):
        if movie in self.favs:
            self.favs.remove(movie)
            messagebox.showinfo("Success", f"Removed {movie['title']} from favorites!")
            if self.search_txt.get() == "Search movies...":
                self.show_movies(self.favs)

    def show_details(self, movie):
        win = tk.Toplevel(self.root)
        win.geometry("600x800")
        win.title(movie.get('title', 'Movie Details'))
        win.configure(bg='#1a1a1a')
        win.grab_set()
        
        box = tk.Frame(win, bg='#1a1a1a', padx=20, pady=20)
        box.pack(fill='both', expand=True)
        
        if movie.get('poster_path'):
            try:
                resp = requests.get(f"{self.img_url}{movie['poster_path']}")
                img = Image.open(BytesIO(resp.content)).resize((300, 450))
                photo = ImageTk.PhotoImage(img)
                tk.Label(box, image=photo, bg='#1a1a1a').pack(pady=20)
                box.image = photo
            except:
                tk.Label(box, text="Image Not Available", fg='white', bg='#1a1a1a').pack(pady=20)
        
        tk.Label(box, text=movie['title'], fg='white', bg='#1a1a1a',
                font=('Helvetica', 16, 'bold')).pack(pady=10)
        tk.Label(box, text=f"Rating: {movie.get('vote_average', 0):.1f}/10",
                fg='#b3b3b3', bg='#1a1a1a', font=('Helvetica', 12)).pack(pady=5)
        tk.Label(box, text=movie.get('overview', 'No description available'),
                fg='#b3b3b3', bg='#1a1a1a', wraplength=500, font=('Helvetica', 11)).pack(pady=20)
        
        ttk.Button(box, text="Close", style='Cat.TButton',
                  command=win.destroy).pack(pady=10)

    def scroll(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def resize(self, event):
        self.canvas.itemconfig(1, width=self.canvas.winfo_width())

    def clear_txt(self, entry):
        if entry.get() == "Search movies...":
            entry.delete(0, tk.END)

    def show_movies(self, movies):
        for widget in self.content.winfo_children():
            widget.destroy()
        
        for i, movie in enumerate(movies):
            is_fav = movie in self.favs
            self.make_card(movie, i // 3, i % 3, is_fav)
            self.content.grid_columnconfigure(i % 3, weight=1)

    def add_fav(self, movie):
        if movie not in self.favs:
            self.favs.append(movie)
            messagebox.showinfo("Success", f"Added {movie['title']} to favorites!")

    def search(self):
        query = self.search_txt.get()
        if query and query != "Search movies...":
            self.get_movies("search/movie", {"query": query})

    def get_trending(self): self.get_movies("trending/movie/day")
    def get_popular(self): self.get_movies("movie/popular")
    def get_top(self): self.get_movies("movie/top_rated")

if __name__ == "__main__":
    root = ThemedTk(theme="black")
    app = App(root)
    root.mainloop()