import tkinter as tk

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
