import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import json


class RoomMapper:
    def __init__(self, root):
        self.root = root
        self.root.title("Room Shape Mapper")

        # Calibration points
        self.calibration = {
            'points': [
                {
                    'vacuum': {'x': 25500, 'y': 25500},
                    'map': {'x': 305, 'y': 167}
                },
                {
                    'vacuum': {'x': 26500, 'y': 25500},
                    'map': {'x': 325, 'y': 167}
                },
                {
                    'vacuum': {'x': 25500, 'y': 26500},
                    'map': {'x': 305, 'y': 147}
                }
            ]
        }

        # Initialize points list and state variables
        self.points = []
        self.image = None
        self.photo = None
        self.is_drawing = False

        # Create main frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create buttons frame
        self.button_frame = tk.Frame(self.main_frame)
        self.button_frame.pack(side=tk.TOP, fill=tk.X)

        # Add buttons with improved layout
        buttons = [
            ("Load Image", self.load_image),
            ("Clear Points", self.clear_points),
            ("Generate YAML", self.generate_yaml),
            ("Undo Last Point", self.undo_last_point),
            ("Close Shape", self.close_shape)
        ]

        for text, command in buttons:
            tk.Button(self.button_frame, text=text, command=command,
                      padx=10, pady=5).pack(side=tk.LEFT, padx=5, pady=5)

        # Create canvas with scrollbars
        self.canvas_frame = tk.Frame(self.main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.h_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL)
        self.v_scrollbar = tk.Scrollbar(self.canvas_frame)
        self.canvas = tk.Canvas(self.canvas_frame, bg='white',
                                xscrollcommand=self.h_scrollbar.set,
                                yscrollcommand=self.v_scrollbar.set)

        # Configure scrollbars
        self.h_scrollbar.config(command=self.canvas.xview)
        self.v_scrollbar.config(command=self.canvas.yview)

        # Pack scrollbars and canvas
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind events
        self.canvas.bind("<Button-1>", self.add_point)
        self.canvas.bind("<Motion>", self.update_preview_line)
        self.canvas.bind("<Button-3>", self.close_shape)  # Right-click to close shape

        # Add mouse wheel zoom support
        self.canvas.bind("<Control-MouseWheel>", self.zoom)

        # Create coordinates display
        self.coord_var = tk.StringVar()
        self.coord_label = tk.Label(self.main_frame, textvariable=self.coord_var)
        self.coord_label.pack(side=tk.BOTTOM, fill=tk.X)

    def zoom(self, event):
        """Handle mouse wheel zoom events"""
        scale = 1.1 if event.delta > 0 else 0.9
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.canvas.scale("all", x, y, scale, scale)

    def load_image(self):
        """Load and display an image file"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if file_path:
            try:
                self.image = Image.open(file_path)
                self.photo = ImageTk.PhotoImage(self.image)

                # Configure canvas scrolling region
                self.canvas.config(scrollregion=(0, 0, self.image.width, self.image.height))
                self.canvas.delete("all")
                self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

                self.clear_points()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {str(e)}")

    def add_point(self, event):
        """Add a point at the clicked location"""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        self.points.append([x, y])
        self.draw_point(x, y)

        if len(self.points) > 1:
            self.draw_line(self.points[-2][0], self.points[-2][1], x, y)

        self.is_drawing = True
        self.update_coordinates_display()

    def draw_point(self, x, y, color='red'):
        """Draw a point on the canvas"""
        point_radius = 3
        self.canvas.create_oval(
            x - point_radius, y - point_radius,
            x + point_radius, y + point_radius,
            fill=color, tags='points'
        )

    def draw_line(self, x1, y1, x2, y2, color='blue', tags='lines'):
        """Draw a line on the canvas"""
        self.canvas.create_line(x1, y1, x2, y2, fill=color, tags=tags)

    def update_preview_line(self, event):
        """Update the preview line while moving the mouse"""
        if self.points and self.is_drawing:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)

            # Delete old preview line
            self.canvas.delete('preview_line')

            # Draw new preview line
            last_point = self.points[-1]
            self.draw_line(last_point[0], last_point[1], x, y,
                           color='gray', tags='preview_line')

    def close_shape(self, event=None):
        """Close the shape by connecting the last point to the first"""
        if len(self.points) > 2:
            first_point = self.points[0]
            last_point = self.points[-1]
            self.draw_line(last_point[0], last_point[1],
                           first_point[0], first_point[1])
            self.is_drawing = False

    def clear_points(self):
        """Clear all points and lines from the canvas"""
        self.points = []
        self.canvas.delete('points', 'lines', 'preview_line')
        self.is_drawing = False
        self.update_coordinates_display()

    def undo_last_point(self):
        """Remove the last point and redraw the shape"""
        if self.points:
            self.points.pop()
            self.canvas.delete('points', 'lines', 'preview_line')

            # Redraw remaining points and lines
            for i, (x, y) in enumerate(self.points):
                self.draw_point(x, y)
                if i > 0:
                    prev_x, prev_y = self.points[i - 1]
                    self.draw_line(prev_x, prev_y, x, y)

            self.update_coordinates_display()

    def calculate_transformation(self):
        """Calculate the transformation matrix from map to vacuum coordinates"""
        cal_points = self.calibration['points']

        # Calculate scales
        scales_x = []
        scales_y = []
        for i in range(len(cal_points)):
            for j in range(i + 1, len(cal_points)):
                point1 = cal_points[i]
                point2 = cal_points[j]

                if point1['map']['x'] != point2['map']['x']:
                    scale_x = (point2['vacuum']['x'] - point1['vacuum']['x']) / (
                            point2['map']['x'] - point1['map']['x'])
                    scales_x.append(scale_x)

                if point1['map']['y'] != point2['map']['y']:
                    scale_y = (point2['vacuum']['y'] - point1['vacuum']['y']) / (
                            point2['map']['y'] - point1['map']['y'])
                    scales_y.append(scale_y)

        scale_x = sum(scales_x) / len(scales_x) if scales_x else 1
        scale_y = sum(scales_y) / len(scales_y) if scales_y else 1

        # Calculate offset using first calibration point
        reference_point = cal_points[0]
        offset_x = reference_point['vacuum']['x'] - (reference_point['map']['x'] * scale_x)
        offset_y = reference_point['vacuum']['y'] - (reference_point['map']['y'] * scale_y)

        return {
            'scale_x': scale_x,
            'scale_y': scale_y,
            'offset_x': offset_x,
            'offset_y': offset_y
        }

    def translate_point(self, x, y, transformation):
        """Convert map coordinates to vacuum coordinates"""
        vacuum_x = round((x * transformation['scale_x']) + transformation['offset_x'])
        vacuum_y = round((y * transformation['scale_y']) + transformation['offset_y'])
        return [vacuum_x, vacuum_y]

    def generate_yaml(self):
        """Generate YAML output from the points"""
        if not self.points:
            messagebox.showwarning("Warning", "No points to generate YAML from!")
            return

        transformation = self.calculate_transformation()
        vacuum_coords = [self.translate_point(x, y, transformation)
                         for x, y in self.points]

        yaml_output = "outline: ["
        yaml_output += ", ".join(f"[ {point[0]}, {point[1]} ]"
                                 for point in vacuum_coords)
        yaml_output += "]"

        # Create a popup window with the YAML
        popup = tk.Toplevel(self.root)
        popup.title("Generated YAML")
        popup.geometry("600x400")

        # Add text widget with scrollbar
        text_frame = tk.Frame(popup)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget = tk.Text(text_frame, wrap=tk.WORD,
                              yscrollcommand=scrollbar.set)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, yaml_output)

        scrollbar.config(command=text_widget.yview)

        # Add copy button
        def copy_to_clipboard():
            self.root.clipboard_clear()
            self.root.clipboard_append(yaml_output)
            self.root.update()
            messagebox.showinfo("Success", "YAML copied to clipboard!")

        tk.Button(popup, text="Copy to Clipboard",
                  command=copy_to_clipboard).pack(pady=5)

    def update_coordinates_display(self):
        """Update the coordinate display label"""
        if self.points:
            coords_text = "Points: " + " → ".join(
                f"({int(x)}, {int(y)})" for x, y in self.points)
            self.coord_var.set(coords_text)
        else:
            self.coord_var.set("No points selected")


if __name__ == "__main__":
    root = tk.Tk()
    app = RoomMapper(root)
    root.mainloop()