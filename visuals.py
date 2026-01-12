from pathlib import Path
from PIL import Image, ImageDraw

PALETTE = {
  "0":  "#E84C49",  # Red
  "1":  "#F5A23D",  # Orange
  "2":  "#F8E64C",  # Yellow
  "3":  "#7CCB5F",  # Green
  "4":  "#4DA3FF",  # Blue
  "5":  "#A364E5",  # Purple
  "6":  "#D95BA5",  # Pink
  "7":  "#CFCFCF",  # Light Gray
  "8":  "#B18A5F",  # Brown
  "9":  "#32D3C8",  # Teal
  "10": "#7BD0C4",  # Soft Aqua
  "11": "#FF6E3A",  # Bright Coral
  "12": "#FCE96A",  # Bright Lemon
  "13": "#54E346",  # Lime Green
  "14": "#1FA774",  # Deep Mint
  "15": "#3F57FF",  # Bold Indigo Blue
  "16": "#B95FFF",  # Vivid Lavender
  "17": "#FF7BDD",  # Hot Magenta
  "18": "#8C8C8C",  # Medium Gray
  "19": "#D6C18F",  # Sand / Desert
  "20": "#00F0FF",  # Electric Cyan
}

CANVAS = 500 
OUTER_W = max(8, CANVAS // 60)
GRID_W = max(2, OUTER_W // 2)

def parse_board_from_txt(txt_path: Path):
    rows = []
    for line in txt_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")] if "," in line else line.split()
        rows.append([str(p) for p in parts if p != ""])

    if len(set(len(r) for r in rows)) != 1:
        raise ValueError("Inconsistent row lengths in board representation.")
    return rows # list[list[str]]

def compute_layout(nr, nc, size=CANVAS, outer=OUTER_W, grid=GRID_W):
    total_grid_x = (nc - 1) * grid
    total_grid_y = (nr - 1) * grid
    usable_w = size - 2 * outer - total_grid_x
    usable_h = size - 2 * outer - total_grid_y
    if usable_w <= 0 or usable_h <= 0:
        raise ValueError("Grid/border too thick for canvas size.")

    base_cw, rem_w = divmod(usable_w, nc)
    base_ch, rem_h = divmod(usable_h, nr)

    # distribute remainder: first rem_w cols get +1 pixel
    col_widths = [base_cw + (1 if c < rem_w else 0) for c in range(nc)]
    row_heights = [base_ch + (1 if r < rem_h else 0) for r in range(nr)]

    x = [outer]
    for c in range(nc):
        x.append(x[-1] + col_widths[c])
        if c < nc - 1:
            x[-1] += grid

    y = [outer]
    for r in range(nr):
        y.append(y[-1] + row_heights[r])
        if r < nr - 1:
            y[-1] += grid

    return x, y

def generate_board_visuals(board_rows, output_path: Path = Path("./outputs"), save_image=False, display=False):
    nr, nc = len(board_rows), len(board_rows[0])

    img = Image.new("RGB", (CANVAS, CANVAS), color="white")
    d = ImageDraw.Draw(img)

    x_edges, y_edges = compute_layout(nr, nc)

    # Drawing cells
    for r in range(nr):
        for c in range(nc):
            raw_val = board_rows[r][c]
            s = str(raw_val)
            if "Q" in s or "q" in s:
                s = s.replace("Q", "").replace("q", "")
            s = s.strip()

            if s not in PALETTE:
                raise KeyError(f"Cell ({r},{c}) value '{raw_val}' not found in PALETTE.")
            
            color_hex = PALETTE[s]
            color_rgb = tuple(int(color_hex[i:i+2], 16) for i in (1, 3, 5))

            x0 = x_edges[c]
            x1 = x_edges[c + 1] - (GRID_W if c < nc - 1 else 0)
            y0 = y_edges[r]
            y1 = y_edges[r + 1] - (GRID_W if r < nr - 1 else 0)
            d.rectangle([x0, y0, x1, y1], fill=color_rgb)

    # Draw inner grid lines (thin)
    # verticals between cells
    for c in range(1, nc):
        x = x_edges[c] - GRID_W
        d.rectangle([x, OUTER_W, x + GRID_W - 1, CANVAS - OUTER_W - 1], fill="black")
    # horizontals between cells
    for r in range(1, nr):
        y = y_edges[r] - GRID_W
        d.rectangle([OUTER_W, y, CANVAS - OUTER_W - 1, y + GRID_W - 1], fill="black")

    # Drawing queens if existent
    queen_path = Path("./images/queen.png")
    if queen_path.exists():
        queen_path_img = Image.open(queen_path).convert("RGBA")
        for r in range(nr):
            for c in range(nc):
                if "Q" in str(board_rows[r][c]):
                    # Resize queen image to fit cell
                    cell_w = x_edges[c + 1] - x_edges[c] - (GRID_W if c < nc - 1 else 0)
                    cell_h = y_edges[r + 1] - y_edges[r] - (GRID_W if r < nr - 1 else 0)
                    queen_resized = queen_path_img.resize((cell_w, cell_h), Image.LANCZOS)

                    # Paste queen image onto board
                    img.paste(queen_resized, (x_edges[c], y_edges[r]), queen_resized)

    # Outer border (thicker)
    ow = OUTER_W
    d.rectangle([0, 0, CANVAS - 1, CANVAS - 1], outline="black", width=ow)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if save_image:
        img.save(output_path, "PNG")
    if display:
        img.show()
    
if __name__ == "__main__":
    # Example usage

    board = [
        ["Q0", "1", "2", "3", "4", "5", "6", "7"],
        ["1", "Q2", "3", "4", "5", "6", "7", "0"],
        ["2", "3", "Q4", "5", "6", "7", "0", "1"],
        ["3", "4", "5", "Q6", "7", "0", "1", "2"],
        ["4", "5", "6", "7", "Q0", "1", "2", "3"],
        ["5", "6", "7", "0", "1", "Q2", "3", "4"],
        ["6", "7", "0", "1", "2", "3", "Q4", "5"],
        ["7", "0", "1", "2", "3", "4", "5", "Q6"],
    ]

    generate_board_visuals(board, display=True)