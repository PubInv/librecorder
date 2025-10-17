import requests
import mimetypes
import os
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox

SERVER = "http://microlab.parccommons.org"   # Flask server from app.py

def pick_and_upload():
    root = tk.Tk()
    root.withdraw()  # hide empty window

    # Step 1: Pick a file
    path = filedialog.askopenfilename(
        filetypes=[("JPEG images", "*.jpg"), ("JPEG images", "*.jpeg"), ("Text files", "*.txt"), ("All files", "*.*")]
    )
    if not path:
        print("No file selected.")
        return

    # Step 2: Case selection
    case_id = simpledialog.askstring(
        "Case ID",
        "Enter an existing Case ID, or leave blank to create a new case:"
    )

    data = {"case_id": case_id} if case_id else {}

    # Step 3: Upload the file
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        mime = "application/octet-stream"

    with open(path, "rb") as f:
        r = requests.post(
            f"{SERVER}/upload",
            files={"file": (os.path.basename(path), f, mime)},
            data=data
        )

    if not r.ok:
        messagebox.showerror("Upload Failed", r.text)
        return

    resp = r.json()
    case_id = resp["case_id"]  # use actual ID returned (new or existing)

    note_text = simpledialog.askstring(
        "Add Note",
        "Enter a note to attach to this case (leave blank to skip):"
    )

    if note_text:
        r2 = requests.post(
            f"{SERVER}/upload",
            files={"file": ("note.txt", note_text.encode("utf-8"), "text/plain")},
            data={"case_id": case_id}
        )
        if r2.ok:
            messagebox.showinfo("Note Added", f"Note uploaded to case {case_id}")
        else:
            messagebox.showerror("Note Upload Failed", r2.text)

    # --- Automatically call processing if JPEG ---
    ext = os.path.splitext(path)[1].lower()
    if ext in [".jpg", ".jpeg"]:
        proc_resp = requests.post(
            f"{SERVER}/process",
            data={
                "case_id": case_id,
                "filename": resp["filename"],
                "processor": "mean_pixel"
            }
        )
        if proc_resp.ok:
            result = proc_resp.json().get("result")
            print("Processing result:", result)
            messagebox.showinfo("Processing Complete", f"Mean pixel: {result.get('mean_pixel')}")
        else:
            print("Processing failed:", proc_resp.text)
            messagebox.showerror("Processing Failed", proc_resp.text)

    note_text = simpledialog.askstring(
        "Add Note",
        "Enter a note to attach to this case (leave blank to skip):"
    )

    if note_text:
        r2 = requests.post(
            f"{SERVER}/upload",
            files={"file": ("note.txt", note_text.encode("utf-8"), "text/plain")},
            data={"case_id": case_id}
        )
        if r2.ok:
            messagebox.showinfo("Note Added", f"Note uploaded to case {case_id}")
        else:
            messagebox.showerror("Note Upload Failed", r2.text)


    messagebox.showinfo("Upload Complete", f"File uploaded to case {case_id}")
    print("Response:", resp)

if __name__ == "__main__":
    pick_and_upload()
