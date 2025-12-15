# ================================================================
# admin_pages.py — Modern UI + functional manage pets (edit/delete)
# ================================================================
import os
import webbrowser
from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image

from app.config import ASSETS_DIR, BASE_DIR, IMAGES_DIR
from app.controllers import AdminController
from app.services.pet_components import load_pet_image

ctk.set_appearance_mode("light")

LOGO_FILE = "FurEver_Home_Logo.png"
_HEADER_LOGO = None
PROJECT_ROOT = Path(BASE_DIR)
ASSETS_ROOT = Path(ASSETS_DIR)
IMAGES_ROOT = Path(IMAGES_DIR)


def _get_header_logo(size=(130, 70)):
    """
    Lazy-load the shared header logo so it is reused across screens.
    """
    global _HEADER_LOGO
    if _HEADER_LOGO is not None:
        return _HEADER_LOGO if _HEADER_LOGO else None

    try:
        path = ASSETS_ROOT / LOGO_FILE
        if not path.exists():
            _HEADER_LOGO = False
            return None
        img = Image.open(path).convert("RGBA")
        _HEADER_LOGO = ctk.CTkImage(img, size=size)
        return _HEADER_LOGO
    except Exception:
        _HEADER_LOGO = False
        return None


# ================================================================
# HEADER BUILDER (used by all pages)
# ================================================================
def make_header(parent, title="Admin Dashboard", quote=None):
    header = ctk.CTkFrame(parent, fg_color="#042b66", corner_radius=0)
    header.pack(fill="x")

    row = ctk.CTkFrame(header, fg_color="#042b66")
    row.pack(side="left", padx=25, pady=10)

    logo = _get_header_logo()
    if logo:
        logo_lbl = ctk.CTkLabel(row, image=logo, text="")
        logo_lbl.image = logo
        logo_lbl.pack(side="left", padx=(0, 14))

    text_block = ctk.CTkFrame(row, fg_color="#042b66")
    text_block.pack(side="left")
    ctk.CTkLabel(text_block, text=title, font=("Georgia", 34, "bold"), text_color="white").pack(anchor="w")
    if quote:
        ctk.CTkLabel(text_block, text=quote, font=("Georgia", 14), text_color="white").pack(anchor="w")


# ================================================================
# ADMIN HOME PAGE
# ================================================================
class AdminHomePage(ctk.CTkFrame):
    def __init__(self, master, app, switch_frame=None):
        super().__init__(master)
        self.app = app
        self.switch_frame = switch_frame
        self.controller = AdminController()
        self.manage_category = "All"

        self.configure(fg_color="#f2f5fa")
        self.pack(fill="both", expand=True)

        make_header(self, "Furever Home", "Manage your system efficiently.")

        container = ctk.CTkFrame(self, fg_color="#f2f5fa")
        container.pack(fill="both", expand=True)

        sidebar = ctk.CTkFrame(container, width=230, fg_color="#d9e6f2", corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(sidebar, text="Menu", font=("Georgia", 24, "bold"), text_color="#072658").pack(pady=(20, 10))

        def sb_btn(text, command):
            return ctk.CTkButton(
                sidebar,
                text=text,
                width=200,
                height=44,
                fg_color="#1b63d1",
                hover_color="#154ea8",
                font=("Georgia", 14),
                command=command,
            )

        sb_btn("Dashboard", self.show_dashboard).pack(pady=5)
        sb_btn("Requests", self.show_requests).pack(pady=5)
        sb_btn("Notifications", self.show_notifications).pack(pady=5)
        sb_btn("Manage Pets", self.show_manage_pets).pack(pady=5)
        sb_btn("Adoption History", self.show_history).pack(pady=5)
        sb_btn("Pending Admins", self.show_pending_admins).pack(pady=5)
        sb_btn("Profile", self.show_profile).pack(pady=5)
        sb_btn("Help Center", self.show_help_center).pack(pady=5)
        sb_btn("About Us", self.show_about).pack(pady=5)

        # Move the Logout button to the bottom by adding padx and pady adjustments
        ctk.CTkButton(
            sidebar,
            text="Logout",
            fg_color="#d64545",
            hover_color="#b23333",
            width=180,
            height=44,
            font=("Georgia", 14),
            command=app.logout,
        ).pack(side="bottom", pady=30)

        self.content = ctk.CTkFrame(container, fg_color="#f2f5fa")
        self.content.pack(side="left", fill="both", expand=True)

        self.show_dashboard()

    # =============================================================
    def clear(self):
        for w in list(self.content.winfo_children()):
            w.destroy()

    def _get_admin_id(self):
        user = self.app.current_user or {}
        return user.get("id") or user.get("admin_id")

    def _load_icon(self, filename, size=(22, 22)):
        """
        Small utility to load icon assets safely.
        """
        try:
            path = ASSETS_ROOT / filename
            if not path.exists():
                return None
            img = Image.open(path).convert("RGBA")
            return ctk.CTkImage(img, size=size)
        except Exception:
            return None

    # =============================================================
    # 1. DASHBOARD
    # =============================================================
    def show_dashboard(self):
        self.clear()
        bg = ctk.CTkFrame(self.content, fg_color="#06215A")
        bg.pack(fill="both", expand=True)

        scroll = ctk.CTkScrollableFrame(bg, fg_color="#06215A", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=16, pady=12)

        ctk.CTkLabel(scroll, text="Dashboard Overview", font=("Georgia", 42, "bold"), text_color="white").pack(
            anchor="center", pady=(16, 4)
        )
        ctk.CTkLabel(scroll, text="Quick insights about the system status.", font=("Georgia", 18), text_color="white").pack(
            anchor="center", pady=(0, 18)
        )

        stats_container = ctk.CTkFrame(scroll, fg_color="#06215A")
        stats_container.pack(anchor="center", pady=(4, 18))

        def stat_card(title, value, accent="#1E63D1"):
            card = ctk.CTkFrame(stats_container, fg_color="white", corner_radius=24, width=230, height=140)
            card.pack_propagate(False)
            card.pack(side="left", padx=14)
            accent_bar = ctk.CTkFrame(card, fg_color=accent, width=10, corner_radius=12)
            accent_bar.pack(fill="y", side="left", padx=(0, 10), pady=14)
            body = ctk.CTkFrame(card, fg_color="white")
            body.pack(fill="both", expand=True, padx=4, pady=8)
            ctk.CTkLabel(body, text=title, font=("Georgia", 16, "bold"), text_color="#0f172a").pack(anchor="w")
            ctk.CTkLabel(body, text=str(value), font=("Georgia", 34, "bold"), text_color=accent).pack(anchor="w", pady=(4, 0))
            ctk.CTkLabel(body, text="Updated now", font=("Georgia", 11), text_color="#64748b").pack(anchor="w", pady=(4, 0))

        try:
            snapshot = self.controller.dashboard_snapshot()
        except Exception:
            snapshot = {
                "pets": [],
                "requests": [],
                "adoption_history": [],
                "stats": {
                    "available_pets": 0,
                    "requests": 0,
                    "adoptions": 0,
                    "requests_by_status": {},
                    "availability": {},
                },
            }

        stats = (snapshot or {}).get("stats", {}) or {}
        pets = stats.get("available_pets", 0)
        reqs = stats.get("requests", 0)
        adoptions = stats.get("adoptions", 0)

        stat_card("Available Pets", pets)
        stat_card("Requests", reqs)
        stat_card("Adoptions", adoptions)

        available_pets = (snapshot or {}).get("pets", []) or []
        adoption_history = (snapshot or {}).get("adoption_history", []) or []
        all_requests = (snapshot or {}).get("requests", []) or []
        status_counts = stats.get("requests_by_status", {}) or {}

        pending_requests = status_counts.get("pending", 0)
        approved_requests = status_counts.get("approved", 0) or len(adoption_history)
        rejected_requests = status_counts.get("rejected", 0)

        availability = stats.get("availability", {}) or {}
        if not availability:
            availability = {"No Data": 0}

        top_breeds = [
            ("Aspins", 18),  # predefined sample insight
            ("Shih Tzu", 12),
            ("Persian Mix", 9),
            ("Golden Retriever", 8),
            ("Siamese", 7),
        ]

        top_months = [
            ("March", 22),  # predefined sample insight
            ("July", 19),
            ("December", 17),
            ("May", 14),
            ("January", 12),
        ]

        adoption_breakdown = [
            ("Approved", approved_requests),
            ("Pending", pending_requests),
            ("Rejected", rejected_requests),
        ]

        rating_average = 4.6
        rating_counts = {5: 48, 4: 34, 3: 14, 2: 6, 1: 2}
        total_ratings = sum(rating_counts.values())

        insights = ctk.CTkFrame(scroll, fg_color="#06215A")
        insights.pack(fill="both", expand=True, padx=10, pady=(0, 20))
        insights.grid_columnconfigure(0, weight=1)
        insights.grid_columnconfigure(1, weight=1)

        def make_card(row, col, title):
            card = ctk.CTkFrame(insights, fg_color="white", corner_radius=22)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            ctk.CTkLabel(card, text=title, font=("Georgia", 20, "bold"), text_color="#06215A").pack(
                anchor="w", padx=16, pady=(14, 6)
            )
            return card

        def render_bar_list(parent, data, color="#1E63D1"):
            max_val = max((v for _n, v in data), default=0) or 1
            for name, val in data:
                row = ctk.CTkFrame(parent, fg_color="white")
                row.pack(fill="x", pady=4, padx=10)
                ctk.CTkLabel(row, text=name, font=("Georgia", 13), text_color="#111").pack(side="left")
                bar_bg = ctk.CTkFrame(row, fg_color="#e5e7eb", height=12)
                bar_bg.pack(side="left", fill="x", expand=True, padx=8)
                bar_bg.pack_propagate(False)
                bar_width = max(8, int((val / max_val) * 220))
                ctk.CTkFrame(bar_bg, fg_color=color, height=12, width=bar_width).pack(side="left", fill="y")
                ctk.CTkLabel(row, text=str(val), font=("Georgia", 12, "bold"), text_color="#06215A").pack(
                    side="right", padx=4
                )

        breeds_card = make_card(0, 0, "Most Adopted Breeds")
        render_bar_list(breeds_card, top_breeds, color="#0EA5E9")
        ctk.CTkLabel(
            breeds_card,
            text="Top adopters prefer mixes and friendly small breeds.",
            font=("Georgia", 12),
            text_color="#475569",
        ).pack(anchor="w", padx=16, pady=(2, 10))

        months_card = make_card(0, 1, "Months with Highest Adoptions")
        render_bar_list(months_card, top_months, color="#A855F7")
        ctk.CTkLabel(
            months_card,
            text="Seasonal peaks help plan outreach and vet schedules.",
            font=("Georgia", 12),
            text_color="#475569",
        ).pack(anchor="w", padx=16, pady=(2, 10))

        adoption_card = make_card(1, 0, "Adoptions (Live)")
        total_req = max(1, len(all_requests))
        bar_wrap = ctk.CTkFrame(adoption_card, fg_color="#f8fafc", corner_radius=12)
        bar_wrap.pack(fill="x", padx=12, pady=(6, 10))
        stacked = ctk.CTkFrame(bar_wrap, fg_color="#e5e7eb", height=18, corner_radius=9)
        stacked.pack(fill="x", expand=True, padx=10, pady=10)
        stacked.pack_propagate(False)
        segments = [
            ("#22C55E", approved_requests),
            ("#F59E0B", pending_requests),
            ("#EF4444", rejected_requests),
        ]
        for color, count in segments:
            if count <= 0:
                continue
            width = max(6, int((count / total_req) * 420))
            ctk.CTkFrame(stacked, fg_color=color, height=18, width=width, corner_radius=9).pack(side="left", padx=1)
        legend = ctk.CTkFrame(adoption_card, fg_color="white")
        legend.pack(anchor="w", padx=14, pady=(4, 10))
        for label, color, count in [
            ("Approved", "#22C55E", approved_requests),
            ("Pending", "#F59E0B", pending_requests),
            ("Rejected", "#EF4444", rejected_requests),
        ]:
            row = ctk.CTkFrame(legend, fg_color="white")
            row.pack(anchor="w", pady=2)
            ctk.CTkFrame(row, fg_color=color, width=14, height=14, corner_radius=6).pack(side="left", padx=(0, 6))
            ctk.CTkLabel(row, text=f"{label}: {count}", font=("Georgia", 12), text_color="#0f172a").pack(side="left")
        ctk.CTkLabel(
            adoption_card,
            text=f"Live snapshot: {approved_requests} approved out of {len(all_requests)} total requests.",
            font=("Georgia", 12),
            text_color="#475569",
        ).pack(anchor="w", padx=16, pady=(2, 12))

        availability_card = make_card(1, 1, "Pet Availability")
        render_bar_list(availability_card, list(availability.items()), color="#1E63D1")
        ctk.CTkLabel(
            availability_card,
            text="Breakdown of currently available pets by category.",
            font=("Georgia", 12),
            text_color="#444",
        ).pack(anchor="w", padx=16, pady=(4, 12))

        rating_card = make_card(2, 0, "Adopter Ratings")
        rating_card.grid(columnspan=2, sticky="nsew")
        rating_row = ctk.CTkFrame(rating_card, fg_color="white")
        rating_row.pack(fill="x", padx=12, pady=(0, 6))
        ctk.CTkLabel(
            rating_row, text=f"{rating_average:.1f} / 5.0", font=("Georgia", 28, "bold"), text_color="#06215A"
        ).pack(side="left", padx=(6, 10))
        stars_frame = ctk.CTkFrame(rating_row, fg_color="white")
        stars_frame.pack(side="left")
        full_stars = int(rating_average)
        for idx in range(5):
            char = "★" if idx < full_stars else "☆"
            color = "#FACC15" if idx < full_stars else "#CBD5E1"
            ctk.CTkLabel(stars_frame, text=char, font=("Georgia", 22), text_color=color).pack(side="left", padx=1)
        ctk.CTkLabel(
            rating_row,
            text=f"{total_ratings} responses",
            font=("Georgia", 12),
            text_color="#444",
        ).pack(side="left", padx=12)

        dist_frame = ctk.CTkFrame(rating_card, fg_color="white")
        dist_frame.pack(fill="x", padx=10, pady=(4, 12))
        for stars in range(5, 0, -1):
            count = rating_counts.get(stars, 0)
            row = ctk.CTkFrame(dist_frame, fg_color="white")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{stars} ★", font=("Georgia", 12), text_color="#111").pack(side="left", padx=6)
            bar_bg = ctk.CTkFrame(row, fg_color="#e5e7eb", height=10)
            bar_bg.pack(side="left", fill="x", expand=True, padx=8)
            bar_bg.pack_propagate(False)
            width = max(6, int((count / (max(rating_counts.values()) or 1)) * 220))
            ctk.CTkFrame(bar_bg, fg_color="#FACC15", height=10, width=width).pack(side="left", fill="y")
            ctk.CTkLabel(row, text=str(count), font=("Georgia", 12), text_color="#06215A").pack(side="right", padx=6)

    # =============================================================
    # 2. REQUESTS
    # =============================================================
    def show_requests(self):
        self.clear()
        make_header(self.content, "Adoption Requests", "Tap a request to review and approve/decline.")

        if not hasattr(self, "request_filter_status"):
            # Only show pending requests by default so resolved items drop off this list
            self.request_filter_status = "Pending"

        # Bright hero + rounded shell (match adoption history/sign-up style)
        hero = ctk.CTkFrame(self.content, fg_color="#00156A")
        hero.pack(fill="both", expand=True)

        ctk.CTkLabel(hero, text="Adoption Requests", font=("Georgia", 44, "bold"), text_color="white").pack(
            pady=(22, 6)
        )
        ctk.CTkLabel(hero, text="Review requests, view adopter info, and take action.", font=("Georgia", 16),
                     text_color="#D4FAFF").pack(pady=(0, 18))

        shell = ctk.CTkFrame(hero, width=1040, height=620, corner_radius=40, fg_color="#D4FAFF", border_width=2, border_color="#9EC9FF")
        shell.pack(fill="both", expand=True, padx=22, pady=(0, 26))
        shell.pack_propagate(False)

        list_frame = ctk.CTkScrollableFrame(shell, fg_color="#D4FAFF")
        list_frame.pack(fill="both", expand=True, padx=20, pady=18)

        try:
            data = self.controller.list_requests(getattr(self, "request_filter_status", "All"))
        except Exception:
            data = []

        # Removed "Declined" option since "Rejected" already covers negative outcomes
        status_options = ["All", "Pending", "Approved", "Rejected"]

        toolbar = ctk.CTkFrame(list_frame, fg_color="#D4FAFF")
        toolbar.pack(fill="x", padx=8, pady=(8, 4))
        ctk.CTkLabel(toolbar, text="Filter by Status:", font=("Georgia", 12, "bold"), text_color="#00156A").pack(side="left", padx=(4, 8))
        status_combo = ctk.CTkComboBox(
            toolbar,
            values=status_options,
            width=180,
            command=lambda val: self._set_request_status_filter(val),
        )
        status_combo.pack(side="left", padx=(0, 8))
        try:
            status_combo.set(self.request_filter_status if self.request_filter_status in status_options else "All")
        except Exception:
            status_combo.set("All")

        selected_status = (self.request_filter_status or "All").strip().lower()

        def _normalize_status(val: str) -> str:
            v = (val or "pending").strip().lower()
            return "rejected" if v == "declined" else v

        if selected_status and selected_status != "all":
            data = [
                r for r in data
                if _normalize_status(r.get("status")) == selected_status
            ]

        base_images = IMAGES_ROOT
        base_assets = ASSETS_ROOT

        def resolve_photo(photo_path, size=(80, 80)):
            if not photo_path:
                return None
            normalized = str(photo_path).replace("\\", "/")
            if normalized.startswith("images/"):
                normalized = normalized.split("/", 1)[1]
            candidates = []
            if os.path.isabs(photo_path):
                candidates.append(photo_path)
            candidates.append(str(base_images / normalized))
            candidates.append(str(base_assets / normalized))
            for path in candidates:
                if os.path.exists(path):
                    try:
                        return load_pet_image(path, size=size)
                    except Exception:
                        continue
            return None

        if not data:
            ctk.CTkLabel(list_frame, text="No adoption requests found.", font=("Georgia", 14), text_color="#666").pack(pady=12)
            return

        def open_request_detail(req):
            # ---------------------------
            # LOAD DATA
            # ---------------------------
            try:
                full = self.controller.get_request(req.get("id"))
            except Exception:
                full = req

            status_raw = (full or {}).get("status") or req.get("status", "pending")

            # ---------------------------
            # MAIN WINDOW
            # ---------------------------
            detail = ctk.CTkToplevel(self)
            detail.title("Adoption Request Details")
            detail.geometry("900x820")
            detail.configure(fg_color="#0C2D48")   # dark blue tone
            detail.resizable(False, False)

            # =============================
            #   TWO-TONE BACKGROUND
            # =============================
            top_frame = ctk.CTkFrame(detail, fg_color="#145DA0")  # lighter blue
            top_frame.pack(fill="x", pady=0)

            body_frame = ctk.CTkFrame(detail, fg_color="#FFFFFF")
            body_frame.pack(fill="both", expand=True, pady=(0, 5), padx=5)

            # =============================
            #   HEADER — PET CALLING ADOPTER
            # =============================
            title_text = (
                f"{full.get('pet_name')} is calling {full.get('adopter_name')}!"
                if full else "Adoption Request"
            )

            ctk.CTkLabel(
                top_frame,
                text=title_text,
                font=("Georgia", 26, "bold"),
                text_color="white"
            ).pack(pady=20)

            # ===========================================================
            #   PET ID TAG HEADER
            # ===========================================================
            id_tag = ctk.CTkFrame(body_frame, fg_color="#145DA0", corner_radius=50)
            id_tag.pack(fill="x", padx=40, pady=(20, 0))

            ctk.CTkLabel(
                id_tag,
                text="Adoption Application Details",
                font=("Georgia", 22, "bold"),
                text_color="white"
            ).pack(pady=10)

            # ===========================================================
            #   CALLING CARD AREA
            # ===========================================================
            calling_card = ctk.CTkFrame(body_frame, fg_color="white", corner_radius=20)
            calling_card.pack(fill="x", padx=20, pady=10)

            calling_card.grid_columnconfigure(0, weight=1)
            calling_card.grid_columnconfigure(1, weight=0)
            calling_card.grid_columnconfigure(2, weight=1)


            # --------------------------
            # PET PHOTO (LEFT)
            # --------------------------
            pet_photo = full.get("pet_image_resolved")
            try:
                pet_img = load_pet_image(pet_photo, size=(260, 240))
            except:
                pet_img = None

            pet_photo_frame = ctk.CTkFrame(calling_card, fg_color="white", corner_radius=20)
            pet_photo_frame.grid(row=0, column=0, padx=20, pady=20)

            if pet_img:
                pet_pic = ctk.CTkLabel(
                    pet_photo_frame,
                    image=pet_img,
                    text="",
                    corner_radius=20
                )
                pet_pic.image = pet_img
                pet_pic.pack()
            else:
                ctk.CTkLabel(
                    pet_photo_frame,
                    text="No Pet Photo",
                    width=240,
                    height=200,
                    fg_color="#e5e7eb",
                    text_color="#555",
                    corner_radius=20
                ).pack()


            # ==========================
            # BLUE DIVIDER LINE
            # ==========================
            line = ctk.CTkFrame(calling_card, fg_color="#145DA0", width=4, height=200)
            line.grid(row=0, column=1, padx=10, pady=10)


            # --------------------------
            # ADOPTER PHOTO (RIGHT)
            # --------------------------
            adopter_photo = resolve_photo((full or {}).get("adopter_photo"), size=(240, 240))

            adopter_photo_frame = ctk.CTkFrame(calling_card, fg_color="white", corner_radius=20)
            adopter_photo_frame.grid(row=0, column=2, padx=20, pady=20)

            if adopter_photo:
                adopter_pic = ctk.CTkLabel(
                    adopter_photo_frame,
                    image=adopter_photo,
                    text="",
                    corner_radius=20
                )
                adopter_pic.image = adopter_photo
                adopter_pic.pack()
            else:
                ctk.CTkLabel(
                    adopter_photo_frame,
                    text="No Photo",
                    width=240,
                    height=200,
                    fg_color="#e5e7eb",
                    text_color="#555",
                    corner_radius=20
                ).pack()


            # ===========================================================
            #   DECLINED STAMP (approved overlay removed)
            # ===========================================================
            stamp_img = None
            if status_raw.lower() in ("declined", "rejected"):
                stamp_file = "rejected.png"
                for sp in [ASSETS_ROOT / stamp_file]:
                    if os.path.exists(sp):
                        stamp = Image.open(sp).resize((220, 160))
                        stamp_img = ctk.CTkImage(stamp)
                        break

            if stamp_img:
                stamp_lbl = ctk.CTkLabel(calling_card, image=stamp_img, text="")
                stamp_lbl.image = stamp_img
                stamp_lbl.place(x=300, y=10)

            # ===========================================================
            #   FULL APPLICATION INFO (CENTERED CARD WITH SHADOW)
            # ===========================================================
            # Shadow frame (light gray)
            shadow_frame = ctk.CTkFrame(body_frame, fg_color="#E5E7EB", corner_radius=25)
            shadow_frame.pack(fill="both", expand=False, padx=18, pady=(10, 20))

            # White card on top
            info_frame = ctk.CTkFrame(shadow_frame, fg_color="white", corner_radius=20)
            info_frame.pack(fill="both", expand=True, padx=4, pady=4)

            # Build the info text
            info_text = (
                f"{full.get('pet_name')} ({full.get('breed')})\n\n"
                f"{full.get('reason') or '—'}"
            )

            # Centered label
            info_label = ctk.CTkLabel(
                info_frame,
                text=info_text,
                font=("Georgia", 16),
                text_color="#0F172A",
                justify="center",
                wraplength=700
            )
            info_label.pack(expand=True, pady=30)


            # ===========================================================
            #   ACTION BUTTONS
            # ===========================================================
            buttons = ctk.CTkFrame(detail, fg_color="#0C2D48")
            buttons.pack(fill="x", pady=(5, 15))

        
            # ---------------------------------------
            def do_approve():
                if not messagebox.askyesno("Approve", "Approve this adoption request?"):
                    return
                try:
                    self.controller.approve_request(req.get("id"))
                    messagebox.showinfo("Approved", "Request approved. Pet marked as adopted.")
                except Exception as e:
                    messagebox.showerror("Error", f"Unable to approve request.\n{e}")
                    return

                detail.destroy()
                self.request_filter_status = "Pending"
                self.show_requests()


            def do_decline():
                reason = simpledialog.askstring("Decline Request", "Enter a decline reason (optional):")
                if reason is None:
                    return
                try:
                    self.controller.decline_request(req.get("id"), reason or "")
                    messagebox.showinfo("Declined", "Request declined.")
                except Exception as e:
                    messagebox.showerror("Error", f"Unable to decline request.\n{e}")
                    return

                detail.destroy()
                self.request_filter_status = "Pending"
                self.show_requests()


            def do_delete():
                if status_raw.lower() == "approved":
                    messagebox.showinfo("Not Allowed", "Approved requests are kept for history and cannot be deleted.")
                    return

                if not messagebox.askyesno("Delete Request", "Delete this request? This cannot be undone."):
                    return

                try:
                    ok = self.controller.delete_request(req.get("id"))
                except Exception as e:
                    messagebox.showerror("Error", f"Unable to delete request.\n{e}")
                    return

                if ok:
                    messagebox.showinfo("Deleted", "Request removed.")
                else:
                    messagebox.showerror("Error", "Unable to delete this request.")

                detail.destroy()
                self.request_filter_status = "Pending"
                self.show_requests()



            if status_raw.lower() == "pending":
                ctk.CTkButton(buttons, text="Approve", width=160, fg_color="#16A34A",
                            hover_color="#15803D", command=do_approve).pack(side="left", padx=20)
                ctk.CTkButton(buttons, text="Reject", width=160, fg_color="#DC2626",
                            hover_color="#B91C1C", command=do_decline).pack(side="left", padx=20)

            ctk.CTkButton(buttons, text="Delete", width=150,
                        fg_color="#4B5563", hover_color="#374151",
                        command=do_delete).pack(side="right", padx=20)

        for r in data:
            card = ctk.CTkFrame(list_frame, fg_color="white", corner_radius=18, border_width=1, border_color="#b7d4ff")
            card.pack(fill="x", padx=8, pady=8)
            top = ctk.CTkFrame(card, fg_color="#f8fafc")
            top.pack(fill="x", padx=12, pady=8)
            avatar = resolve_photo(r.get("adopter_photo"), size=(70, 70))
            if avatar:
                lbl = ctk.CTkLabel(top, image=avatar, text="")
                lbl.image = avatar
                lbl.pack(side="left", padx=(0, 12))
            else:
                ctk.CTkLabel(top, text="No Photo", width=70, height=70, fg_color="#e5e7eb", text_color="#666", corner_radius=10).pack(side="left", padx=(0, 12))
            info = ctk.CTkFrame(top, fg_color="#f8fafc")
            info.pack(side="left", fill="both", expand=True)
            ctk.CTkLabel(info, text=r.get("adopter_name",""), font=("Georgia", 16, "bold"), text_color="#111").pack(anchor="w")
            ctk.CTkLabel(info, text=r.get("adopter_email") or "", font=("Georgia", 12), text_color="#334155").pack(anchor="w")
            ctk.CTkLabel(info, text=f"Pet: {r.get('pet_name','')}", font=("Georgia", 13), text_color="#333").pack(anchor="w")
            ctk.CTkLabel(info, text=f"Category: {r.get('category','')}", font=("Georgia", 12), text_color="#555").pack(anchor="w")
            ctk.CTkLabel(info, text=f"Status: {r.get('status','pending').title()} • Requested: {r.get('created_at') or ''}",
                         font=("Georgia", 12), text_color="#555").pack(anchor="w", pady=(2,0))

            ctk.CTkButton(card, text="View / Act", width=140, fg_color="#1E63D1", hover_color="#174DA6",
                          command=lambda req=r: open_request_detail(req)).pack(anchor="e", padx=12, pady=(0, 10))

    def _set_request_status_filter(self, value):
        self.request_filter_status = value or "All"
        self.show_requests()

    # =============================================================
    # NOTIFICATIONS
    # =============================================================
    def show_notifications(self):
        self.clear()
        make_header(self.content, "Notifications", "System alerts and request updates.")

        hero = ctk.CTkFrame(self.content, fg_color="#00156A")
        hero.pack(fill="both", expand=True)

        ctk.CTkLabel(hero, text="Notifications", font=("Georgia", 44, "bold"), text_color="white").pack(
            pady=(22, 6)
        )
        ctk.CTkLabel(hero, text="System alerts and request updates.", font=("Georgia", 16), text_color="#D4FAFF").pack(
            pady=(0, 18)
        )

        shell = ctk.CTkFrame(hero, width=1040, height=620, corner_radius=40, fg_color="#D4FAFF", border_width=2, border_color="#9EC9FF")
        shell.pack(fill="both", expand=True, padx=22, pady=(0, 26))
        shell.pack_propagate(False)

        container = ctk.CTkFrame(shell, fg_color="#D4FAFF")
        container.pack(fill="both", expand=True, padx=18, pady=18)

        toolbar = ctk.CTkFrame(container, fg_color="#D4FAFF")
        toolbar.pack(fill="x", padx=10, pady=(10, 0))

        admin_id = self._get_admin_id()
        if not admin_id:
            messagebox.showerror("Error", "Cannot load notifications: admin id not found.")
            return

        try:
            notifications = self.controller.list_notifications(admin_id)
        except Exception as e:
            messagebox.showerror("Error", f"Unable to fetch notifications.\n{e}")
            return

        def refresh():
            self.show_notifications()

        def mark_all():
            for note in notifications:
                try:
                    self.controller.mark_notification_read(note.get("id"))
                except Exception:
                    continue
            refresh()

        def clear_all():
            if not notifications:
                return
            if not messagebox.askyesno("Clear Notifications", "Remove all notifications?"):
                return
            try:
                self.controller.clear_notifications(admin_id)
            except Exception as e:
                messagebox.showerror("Error", f"Unable to clear notifications.\n{e}")
                return
            refresh()

        ctk.CTkButton(toolbar, text="Refresh", width=120, fg_color="#0B84FF", hover_color="#0861BD",
                      text_color="white", command=refresh).pack(side="right", padx=6)
        ctk.CTkButton(toolbar, text="Mark All Read", width=140, fg_color="#1E63D1", hover_color="#174DA6",
                      text_color="white", command=mark_all).pack(side="right", padx=6)
        ctk.CTkButton(toolbar, text="Clear All", width=120, fg_color="#D64545", hover_color="#B53030",
                      text_color="white", command=clear_all).pack(side="right", padx=6)

        scroll = ctk.CTkScrollableFrame(container, fg_color="white")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        if not notifications:
            ctk.CTkLabel(scroll, text="No notifications yet.", font=("Georgia", 14), text_color="#666").pack(pady=14)
            return

        def mark_one(note_id):
            try:
                self.controller.mark_notification_read(note_id)
                refresh()
            except Exception as e:
                messagebox.showerror("Error", f"Unable to mark notification.\n{e}")

        def remove_one(note_id):
            try:
                self.controller.delete_notification(note_id)
                refresh()
            except Exception as e:
                messagebox.showerror("Error", f"Unable to remove notification.\n{e}")

        for note in notifications:
            bg = "#eef2ff" if not note.get("is_read") else "#f8fafc"
            card = ctk.CTkFrame(scroll, fg_color=bg, corner_radius=12, border_width=1, border_color="#E5E7EB")
            card.pack(fill="x", padx=8, pady=6)

            ctk.CTkLabel(
                card,
                text=note.get("message", ""),
                font=("Georgia", 14),
                text_color="#111",
                wraplength=980,
                justify="left",
            ).pack(anchor="w", padx=12, pady=(10, 4))

            meta_text = f"Received: {note.get('created_at') or '—'}"
            ctk.CTkLabel(card, text=meta_text, font=("Georgia", 11), text_color="#555").pack(
                anchor="w", padx=12, pady=(0, 8)
            )

            btns = ctk.CTkFrame(card, fg_color=bg)
            btns.pack(anchor="e", padx=10, pady=(0, 10))

            if not note.get("is_read"):
                ctk.CTkButton(
                    btns,
                    text="Mark as Read",
                    width=130,
                    fg_color="#1E63D1",
                    hover_color="#174DA6",
                    command=lambda nid=note.get("id"): mark_one(nid),
                ).pack(side="left", padx=5)
            ctk.CTkButton(
                btns,
                text="Remove",
                width=110,
                fg_color="#D64545",
                hover_color="#B53030",
                command=lambda nid=note.get("id"): remove_one(nid),
            ).pack(side="left", padx=5)

    # =============================================================
    # PENDING ADMINS
    # =============================================================
    def show_pending_admins(self):
        self.clear()
        make_header(self.content, "Pending Admins", "Approve or decline new admin sign-ups.")

        hero = ctk.CTkFrame(self.content, fg_color="#00156A")
        hero.pack(fill="both", expand=True)

        ctk.CTkLabel(hero, text="Pending Admins", font=("Georgia", 44, "bold"), text_color="white").pack(
            pady=(22, 6)
        )
        ctk.CTkLabel(hero, text="Review and approve or decline administrator requests.", font=("Georgia", 16),
                     text_color="#D4FAFF").pack(pady=(0, 18))

        shell = ctk.CTkFrame(hero, width=1040, height=620, corner_radius=40, fg_color="#D4FAFF", border_width=2, border_color="#9EC9FF")
        shell.pack(fill="both", expand=True, padx=22, pady=(0, 26))
        shell.pack_propagate(False)

        container = ctk.CTkScrollableFrame(shell, fg_color="#D4FAFF")
        container.pack(fill="both", expand=True, padx=18, pady=18)

        try:
            pending = self.controller.list_pending_admins()
        except Exception:
            pending = []

        if not pending:
            ctk.CTkLabel(container, text="No pending admin requests.", font=("Georgia", 14), text_color="#555").pack(
                pady=12
            )
            return

        for req in pending:
            row = ctk.CTkFrame(container, fg_color="white", corner_radius=16, border_width=1, border_color="#b7d4ff")
            row.pack(fill="x", padx=8, pady=8)

            name = req.get("name", "")
            email = req.get("email", "")
            phone = req.get("phone_number", "")
            birth = req.get("birthdate", "")
            created = req.get("created_at", "")

            top = ctk.CTkFrame(row, fg_color="#f8fafc")
            top.pack(fill="x", padx=10, pady=8)
            ctk.CTkLabel(top, text=name, font=("Georgia", 16, "bold"), text_color="#111").pack(anchor="w")
            ctk.CTkLabel(top, text=email, font=("Georgia", 13), text_color="#444").pack(anchor="w")
            meta = f"Phone: {phone or 'N/A'}    Birthdate: {birth or 'N/A'}    Requested: {created}"
            ctk.CTkLabel(top, text=meta, font=("Georgia", 12), text_color="#666").pack(anchor="w", pady=(4, 0))

            btns = ctk.CTkFrame(row, fg_color="#f8fafc")
            btns.pack(anchor="e", padx=10, pady=(0, 8))

            def approve(pending_id=req.get("pending_id")):
                try:
                    ok = self.controller.approve_pending_admin(pending_id)
                    if ok:
                        messagebox.showinfo("Approved", "Pending admin approved and added.")
                    else:
                        messagebox.showerror("Error", "Pending admin not found.")
                    self.show_pending_admins()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to approve admin.\n{e}")

            def decline(pending_id=req.get("pending_id")):
                if not messagebox.askyesno("Decline", "Decline this admin request?"):
                    return
                try:
                    self.controller.decline_pending_admin(pending_id)
                    messagebox.showinfo("Declined", "Pending admin declined.")
                    self.show_pending_admins()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to decline admin.\n{e}")

            ctk.CTkButton(btns, text="Approve", width=120, fg_color="#16A34A", hover_color="#15803D", command=approve).pack(
                side="left", padx=6
            )
            ctk.CTkButton(btns, text="Decline", width=120, fg_color="#D64545", hover_color="#B53030", command=decline).pack(
                side="left", padx=6
            )

    # =============================================================
    # 3. MANAGE PETS
    # =============================================================
    def show_manage_pets(self):
        self.clear()
        bg = ctk.CTkFrame(self.content, fg_color="#06215A")
        bg.pack(fill="both", expand=True)

        ctk.CTkLabel(bg, text="Manage Pets", font=("Georgia", 42, "bold"), text_color="white").pack(
            anchor="center", pady=(40, 10)
        )
        ctk.CTkLabel(
            bg, text="Add, edit, and manage all pets in the system.", font=("Georgia", 18), text_color="white"
        ).pack(anchor="center", pady=(0, 30))

        # Filter bar
        filter_bar = ctk.CTkFrame(bg, fg_color="#052a6c", corner_radius=14)
        filter_bar.pack(fill="x", padx=60, pady=(0, 18))

        ctk.CTkLabel(filter_bar, text="Category", font=("Georgia", 16), text_color="white").pack(
            side="left", padx=(16, 10), pady=12
        )

        categories = ["All", "dog", "cat"]
        self.category_combo = ctk.CTkComboBox(
            filter_bar,
            values=categories,
            width=180,
            fg_color="#0e3f9a",
            button_color="#0e3f9a",
            text_color="white",
            state="readonly",
        )
        self.category_combo.set(self.manage_category or "All")
        self.category_combo.pack(side="left", pady=10)

        def apply_filter():
            self.manage_category = self.category_combo.get() or "All"
            self._render_manage_cards()

        def reset_filter():
            self.manage_category = "All"
            self.category_combo.set("All")
            self._render_manage_cards()

        ctk.CTkButton(
            filter_bar, text="Filter", width=120, fg_color="#265AAD", hover_color="#73A7FC", command=apply_filter
        ).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(
            filter_bar, text="Reset", width=120, fg_color="#BF2121", hover_color="#374151", command=reset_filter
        ).pack(side="left", padx=6, pady=10)
        ctk.CTkButton(
            filter_bar, text="Add Pet", width=140, fg_color="#0E5A2A", hover_color="#1B8542", command=self.open_add_pet
        ).pack(side="right", padx=12, pady=10)
        

        scroll = ctk.CTkScrollableFrame(bg, fg_color="#06215A", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=60, pady=(10, 40))
        self.manage_scroll = scroll
        self._render_manage_cards()

    def _fetch_pets_for_manage(self, category=None):
        cat = (category or self.manage_category or "All").lower()
        try:
            return self.controller.list_pets(cat)
        except Exception:
            return []

    def _render_manage_cards(self):
        # clear existing grid
        for w in list(self.manage_scroll.winfo_children()):
            w.destroy()

        pets = self._fetch_pets_for_manage()
        if not pets:
            ctk.CTkLabel(self.manage_scroll, text="No pets found.", font=("Georgia", 20), text_color="white").pack(
                pady=30
            )
            return

        grid = ctk.CTkFrame(self.manage_scroll, fg_color="#06215A")
        grid.pack()

        cols = 3
        col = 0
        row = 0

        image_size = (260, 190)

        for pet in pets:
            card = ctk.CTkFrame(grid, fg_color="white", corner_radius=28, width=360, height=550)
            card.grid(row=row, column=col, padx=25, pady=25)
            card.pack_propagate(False)

            try:
                img_path = pet.get("image") or pet.get("photo") or pet.get("photo_path")
                img = load_pet_image(img_path, size=image_size)
                img_label = ctk.CTkLabel(card, image=img, text="", width=image_size[0], height=image_size[1])
                img_label.image = img
                img_label.pack(pady=(20, 10))
            except Exception:
                placeholder = ctk.CTkLabel(card, text="No Image", width=image_size[0], height=image_size[1], fg_color="#D9D9D9")
                placeholder.pack(pady=(20, 10))

            name = pet.get("name", "Unknown")
            ctk.CTkLabel(card, text=name, font=("Georgia", 18, "bold"), text_color="#000").pack(anchor="w", padx=20)

            breed = pet.get("breed", "Unknown")
            age = pet.get("age", "N/A")
            sex = pet.get("sex", "N/A")
            ctk.CTkLabel(
                card, text=f"{breed} • {age} yrs • {sex}", font=("Georgia", 13), text_color="#444"
            ).pack(anchor="w", padx=20)
            status_val = pet.get("status") or "unknown"
            vaccinated_val = pet.get("vaccinated")
            vaccinated_txt = "Yes" if str(vaccinated_val).strip().lower() in ("1", "true", "yes") else "No"
            ctk.CTkLabel(
                card, text=f"Status: {status_val.title() if isinstance(status_val, str) else status_val} • Vaccinated: {vaccinated_txt}",
                font=("Georgia", 12), text_color="#555"
            ).pack(anchor="w", padx=20, pady=(0, 4))

            desc = pet.get("description") or ""
            ctk.CTkLabel(
                card, text=desc, wraplength=300, justify="left", font=("Georgia", 13), text_color="#555"
            ).pack(anchor="w", padx=20, pady=(10, 15))

            btn_frame = ctk.CTkFrame(card, fg_color="white")
            btn_frame.pack(side="bottom", pady=(0, 20))

            ctk.CTkButton(
                btn_frame,
                text="Edit",
                width=130,
                height=36,
                fg_color="#1E63D1",
                hover_color="#174DA6",
                corner_radius=12,
                font=("Georgia", 13, "bold"),
                command=lambda p=pet: self.open_edit_pet(p),
            ).pack(side="left", padx=10)

            ctk.CTkButton(
                btn_frame,
                text="Delete",
                width=130,
                height=36,
                fg_color="#D64545",
                hover_color="#B53030",
                corner_radius=12,
                font=("Georgia", 13, "bold"),
                command=lambda p=pet: self.delete_pet(p),
            ).pack(side="left", padx=10)

            col += 1
            if col >= cols:
                col = 0
                row += 1

    def delete_pet(self, pet):
        pet_id = pet.get("id") if isinstance(pet, dict) else None
        if not pet_id:
            messagebox.showerror("Error", "Missing pet id.")
            return

        img_path = pet.get("photo_path") or pet.get("image") or ""
        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this pet? The record and any stored image will be removed.",
        )
        if not confirm:
            return
        try:
            self.controller.delete_pet(pet_id, img_path)
            messagebox.showinfo("Deleted", "Pet deleted successfully.")
            self._render_manage_cards()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete pet: {e}")

    def open_edit_pet(self, pet):
        if not pet:
            messagebox.showerror("Error", "No pet data available.")
            return

        original_image = pet.get("photo_path") or pet.get("image") or ""
        original_description = pet.get("description") or pet.get("notes") or ""

        win = ctk.CTkToplevel(self)
        win.title("Edit Pet")
        win.geometry("440x560")
        win.resizable(False, False)
        win.grab_set()

        ctk.CTkLabel(win, text="Edit Pet", font=("Georgia", 24, "bold")).pack(pady=(14, 6))

        body = ctk.CTkScrollableFrame(win, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        fields = {}
        labels = ["Name", "Breed", "Age", "Sex"]
        keys = ["name", "breed", "age", "sex"]
        for label, key in zip(labels, keys):
            ctk.CTkLabel(body, text=label, font=("Georgia", 14)).pack(anchor="w", padx=8, pady=(10, 0))
            entry = ctk.CTkEntry(body, width=380)
            entry.insert(0, str(pet.get(key, "") or ""))
            entry.pack(padx=8, pady=(0, 8))
            fields[key] = entry

        # Vaccinated checkbox
        vacc_val = str(pet.get("vaccinated") or "").strip().lower()
        vacc_var = ctk.BooleanVar(value=vacc_val in ("1", "true", "yes"))
        ctk.CTkCheckBox(body, text="Vaccinated", variable=vacc_var).pack(anchor="w", padx=8, pady=(6, 6))

        # Status dropdown
        ctk.CTkLabel(body, text="Status", font=("Georgia", 14)).pack(anchor="w", padx=8, pady=(6, 0))
        status_combo = ctk.CTkComboBox(body, values=["available", "adopted", "pending"], width=200)
        status_combo.set(pet.get("status") or "available")
        status_combo.pack(padx=8, pady=(0, 8))
        fields["status"] = status_combo

        # Image selector
        ctk.CTkLabel(body, text="Image", font=("Georgia", 14)).pack(anchor="w", padx=8, pady=(10, 0))
        image_row = ctk.CTkFrame(body, fg_color="transparent")
        image_row.pack(fill="x", padx=8, pady=(0, 8))
        image_entry = ctk.CTkEntry(image_row, width=270)
        image_entry.insert(0, str(original_image or ""))
        image_entry.pack(side="left", padx=(0, 8))
        fields["image"] = image_entry

        def browse_image():
            path = filedialog.askopenfilename(
                title="Select pet image",
                filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"), ("All Files", "*.*")]
            )
            if path:
                image_entry.delete(0, "end")
                image_entry.insert(0, path)

        ctk.CTkButton(image_row, text="Browse", width=90, command=browse_image).pack(side="left")

        # Description
        ctk.CTkLabel(body, text="Description", font=("Georgia", 14)).pack(anchor="w", padx=8, pady=(10, 0))
        desc_entry = ctk.CTkTextbox(body, width=380, height=100, corner_radius=10)
        desc_entry.insert("1.0", str(original_description or ""))
        desc_entry.pack(padx=8, pady=(0, 8))
        fields["description"] = desc_entry

        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(side="bottom", pady=12, padx=12, fill="x")

        def save_changes():
            name = fields["name"].get().strip()
            breed = fields["breed"].get().strip()
            age = fields["age"].get().strip()
            sex = fields["sex"].get().strip()
            image_val = fields["image"].get().strip() or original_image
            description_val = fields["description"].get("1.0", "end").strip()
            vaccinated_val = 1 if vacc_var.get() else 0
            status_val = fields["status"].get().strip() or pet.get("status") or "available"

            if not all([name, breed, age, sex]):
                messagebox.showerror("Error", "Name, Breed, Age, and Sex are required.")
                return
            try:
                age_int = int(age)
            except ValueError:
                messagebox.showerror("Error", "Age must be a number.")
                return

            try:
                self.controller.update_pet(
                    pet.get("id"),
                    name,
                    breed,
                    age_int,
                    sex,
                    description_val,
                    image_val,
                    current_photo=original_image,
                    category=pet.get("category"),
                    status=status_val,
                    vaccinated=vaccinated_val,
                )
                messagebox.showinfo("Success", "Pet updated successfully.")
                win.destroy()
                self._render_manage_cards()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update pet: {e}")

        ctk.CTkButton(
            btn_frame, text="Save Changes", width=170, height=40, fg_color="#0B84FF", hover_color="#0861BD",
            command=save_changes,
        ).pack(side="left", padx=8)
        ctk.CTkButton(
            btn_frame, text="Cancel", width=120, height=40, fg_color="#D9534F", hover_color="#B9403D",
            command=win.destroy,
        ).pack(side="left", padx=8)

    def open_add_pet(self):
        win = ctk.CTkToplevel(self)
        win.title("Add New Pet")
        win.geometry("440x560")
        win.resizable(False, False)
        win.grab_set()

        ctk.CTkLabel(win, text="Add New Pet", font=("Georgia", 24, "bold")).pack(pady=(14, 6))
        body = ctk.CTkScrollableFrame(win, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        # defaults
        default_category = self.manage_category if self.manage_category and self.manage_category != "All" else "dog"
        fields = {}

        def add_field(label, key, default=""):
            ctk.CTkLabel(body, text=label, font=("Georgia", 14)).pack(anchor="w", padx=8, pady=(10, 0))
            entry = ctk.CTkEntry(body, width=380)
            entry.insert(0, str(default))
            entry.pack(padx=8, pady=(0, 8))
            fields[key] = entry

        add_field("Name", "name", "")
        add_field("Breed", "breed", "")
        add_field("Age", "age", "")

        ctk.CTkLabel(body, text="Sex", font=("Georgia", 14)).pack(anchor="w", padx=8, pady=(10, 0))
        sex_entry = ctk.CTkEntry(body, width=380)
        sex_entry.insert(0, "male/female")
        sex_entry.pack(padx=8, pady=(0, 8))
        fields["sex"] = sex_entry

        vacc_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(body, text="Vaccinated", variable=vacc_var).pack(anchor="w", padx=8, pady=(6, 6))

        ctk.CTkLabel(body, text="Category", font=("Georgia", 14)).pack(anchor="w", padx=8, pady=(10, 0))
        cat_combo = ctk.CTkComboBox(body, values=["dog", "cat"], width=180)
        cat_combo.set(default_category)
        cat_combo.pack(padx=8, pady=(0, 8))
        fields["category"] = cat_combo

        ctk.CTkLabel(body, text="Status", font=("Georgia", 14)).pack(anchor="w", padx=8, pady=(6, 0))
        status_combo = ctk.CTkComboBox(body, values=["available", "adopted", "pending"], width=180)
        status_combo.set("available")
        status_combo.pack(padx=8, pady=(0, 8))
        fields["status"] = status_combo

        # Image selector
        ctk.CTkLabel(body, text="Image", font=("Georgia", 14)).pack(anchor="w", padx=8, pady=(10, 0))
        image_row = ctk.CTkFrame(body, fg_color="transparent")
        image_row.pack(fill="x", padx=8, pady=(0, 8))
        image_entry = ctk.CTkEntry(image_row, width=270)
        image_entry.pack(side="left", padx=(0, 8))
        fields["image"] = image_entry

        def choose_image():
            path = filedialog.askopenfilename(
                title="Select pet image",
                filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"), ("All Files", "*.*")]
            )
            if path:
                image_entry.delete(0, "end")
                image_entry.insert(0, path)

        ctk.CTkButton(image_row, text="Browse", width=90, command=choose_image).pack(side="left")

        # Description (multi-line)
        ctk.CTkLabel(body, text="Description", font=("Georgia", 14)).pack(anchor="w", padx=8, pady=(10, 0))
        desc_box = ctk.CTkTextbox(body, width=380, height=100, corner_radius=10)
        desc_box.pack(padx=8, pady=(0, 8))
        fields["description"] = desc_box

        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(side="bottom", pady=12, padx=12, fill="x")

        def save_new_pet():
            name = fields["name"].get().strip()
            breed = fields["breed"].get().strip()
            age = fields["age"].get().strip()
            sex = fields["sex"].get().strip()
            category = fields["category"].get().strip().lower() or "dog"
            image_val = fields["image"].get().strip()
            description_val = fields["description"].get("1.0", "end").strip()
            vaccinated_val = 1 if vacc_var.get() else 0
            status_val = fields["status"].get().strip() or "available"

            if not all([name, breed, age, sex]):
                messagebox.showerror("Error", "Name, Breed, Age, and Sex are required.")
                return
            try:
                age_int = int(age)
            except ValueError:
                messagebox.showerror("Error", "Age must be a number.")
                return

            try:
                self.controller.add_pet(
                    name=name,
                    category=category,
                    breed=breed,
                    age=age_int,
                    sex=sex,
                    vaccinated=vaccinated_val,
                    status=status_val,
                    image_path=image_val,
                    description=description_val,
                )
                messagebox.showinfo("Success", "Pet added successfully.")
                win.destroy()
                self.manage_category = category if category in ("dog", "cat") else "All"
                if hasattr(self, "category_combo"):
                    self.category_combo.set(self.manage_category)
                self._render_manage_cards()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add pet: {e}")

        ctk.CTkButton(
            btn_frame, text="Save Pet", width=170, height=40, fg_color="#16A34A", hover_color="#15803D",
            command=save_new_pet,
        ).pack(side="left", padx=8)
        ctk.CTkButton(
            btn_frame, text="Cancel", width=120, height=40, fg_color="#D9534F", hover_color="#B9403D",
            command=win.destroy,
        ).pack(side="left", padx=8)

    # =============================================================
    # 5. ADOPTION HISTORY
    # =============================================================
    def show_history(self):
        self.clear()
        make_header(self.content, "Adoption History", "See every adopted pet with full details.")

        # Bright hero + rounded container (mirrors sign-up modal)
        hero = ctk.CTkFrame(self.content, fg_color="#00156A")
        hero.pack(fill="both", expand=True)

        ctk.CTkLabel(hero, text="Adoption History", font=("Georgia", 44, "bold"), text_color="white").pack(
            pady=(22, 6)
        )
        ctk.CTkLabel(hero, text="Every approved adoption with photos and details.", font=("Georgia", 16),
                     text_color="#D4FAFF").pack(pady=(0, 18))

        shell = ctk.CTkFrame(hero, width=1040, height=620, corner_radius=40, fg_color="#D4FAFF", border_width=2, border_color="#9EC9FF")
        shell.pack(fill="both", expand=True, padx=22, pady=(0, 26))
        shell.pack_propagate(False)

        toolbar = ctk.CTkFrame(shell, fg_color="#D4FAFF")
        toolbar.pack(fill="x", padx=26, pady=(18, 6))

        if not hasattr(self, "history_category_filter"):
            self.history_category_filter = "All"

        def set_history_filter(val):
            self.history_category_filter = val or "All"
            self.show_history()

        ctk.CTkLabel(toolbar, text="Category:", font=("Georgia", 13, "bold"), text_color="#00156A").pack(side="left", padx=(0, 8))
        cat_combo = ctk.CTkComboBox(
            toolbar,
            values=["All", "dog", "cat"],
            width=160,
            fg_color="#DDE1E6",
            button_color="#DDE1E6",
            text_color="black",
            command=set_history_filter,
        )
        try:
            cat_combo.set(self.history_category_filter)
        except Exception:
            cat_combo.set("All")
        cat_combo.pack(side="left", padx=(0, 12))

        table = ctk.CTkScrollableFrame(shell, fg_color="#D4FAFF")
        table.pack(fill="both", expand=True, padx=26, pady=(0, 22))

        try:
            hist = self.controller.adoption_history(self.history_category_filter)
        except Exception:
            hist = []

        if not hist:
            ctk.CTkLabel(table, text="No adoptions yet.", font=("Georgia", 14)).pack(pady=12)
            return

        base_images = IMAGES_ROOT
        base_assets = ASSETS_ROOT

        def resolve_pet_image(photo_path, size=(140, 140)):
            """
            Try images/ then assets/, then absolute path for historical rows.
            Handles already-prefixed 'images/<file>' paths.
            """
            if not photo_path:
                return None
            normalized = photo_path.replace("\\", "/")
            if normalized.startswith("images/"):
                normalized = normalized.split("/", 1)[1]
            candidates = []
            if os.path.isabs(photo_path):
                candidates.append(photo_path)
            candidates.append(str(base_images / normalized))
            candidates.append(str(base_assets / normalized))
            for path in candidates:
                if os.path.exists(path):
                    try:
                        return load_pet_image(path, size=size)
                    except Exception:
                        continue
            return None

        for h in hist:
            pet_name = h.get("pet_name") or "Unknown Pet"
            adopted = h.get("adopted_at") or h.get("date") or ""
            adopter = h.get("adopter_name") or "Adopter"
            adopter_email = h.get("adopter_email") or ""
            desc = h.get("description") or "No description provided."
            category = h.get("category") or ""
            breed = h.get("breed") or ""
            age = h.get("age") or "N/A"
            sex = h.get("sex") or "N/A"
            vaccinated = h.get("vaccinated")
            vaccinated_txt = "Vaccinated" if str(vaccinated).lower() in ("1", "true", "yes") else "Not vaccinated"
            status = h.get("status") or ""
            photo = resolve_pet_image(h.get("photo_path"))

            card = ctk.CTkFrame(table, fg_color="white", corner_radius=22, border_width=1, border_color="#b7d4ff")
            card.pack(fill="x", padx=10, pady=10)

            body = ctk.CTkFrame(card, fg_color="white")
            body.pack(fill="both", expand=True, padx=14, pady=14)

            img = ctk.CTkLabel(body, image=photo, text="No Image" if not photo else "")
            img.image = photo
            img.pack(side="left", padx=(0, 16), pady=6)

            info = ctk.CTkFrame(body, fg_color="white")
            info.pack(side="left", fill="both", expand=True)

            header = ctk.CTkFrame(info, fg_color="white")
            header.pack(fill="x")
            ctk.CTkLabel(header, text=pet_name, font=("Georgia", 24, "bold"), text_color="#0f172a").pack(side="left", anchor="w")

            status_lower = str(status).lower()
            badge_color = "#22C55E" if status_lower == "approved" else "#EAB308" if status_lower == "pending" else "#EF4444"
            ctk.CTkLabel(
                header,
                text=status.title() if status else "Status Unknown",
                font=("Georgia", 12, "bold"),
                text_color="white",
                fg_color=badge_color,
                corner_radius=12,
                padx=10,
                pady=4,
            ).pack(side="right", padx=(8, 0))

            meta_parts = [part for part in [category, breed] if part]
            meta = " • ".join(meta_parts) if meta_parts else "Pet details"
            ctk.CTkLabel(info, text=meta, font=("Georgia", 14), text_color="#334155").pack(anchor="w", pady=(6, 6))

            stats_row = ctk.CTkFrame(info, fg_color="white")
            stats_row.pack(fill="x", pady=(0, 4))
            ctk.CTkLabel(stats_row, text=f"Age: {age}", font=("Georgia", 13), text_color="#111").pack(side="left", padx=(0, 10))
            ctk.CTkLabel(stats_row, text=f"Sex: {sex}", font=("Georgia", 13), text_color="#111").pack(side="left", padx=(0, 10))
            ctk.CTkLabel(stats_row, text=vaccinated_txt, font=("Georgia", 12, "bold"), text_color="#0f172a").pack(side="left")

            adopter_line = f"Adopter: {adopter}"
            if adopter_email:
                adopter_line += f" ({adopter_email})"
            ctk.CTkLabel(info, text=adopter_line, font=("Georgia", 12), text_color="#0f172a").pack(anchor="w")
            ctk.CTkLabel(info, text=f"Adopted on: {adopted}", font=("Georgia", 12), text_color="#0f172a").pack(anchor="w", pady=(0, 6))
            ctk.CTkLabel(
                info,
                text=desc,
                font=("Georgia", 13),
                text_color="#1f2937",
                wraplength=760,
                justify="left",
            ).pack(anchor="w", pady=(6, 0))

    # =============================================================
    # 6. PROFILE PAGE
    # =============================================================
    def show_profile(self):
        self.clear()
        make_header(self.content, "My Profile")

        wrapper = ctk.CTkFrame(self.content, fg_color="white")
        wrapper.pack(fill="both", expand=True, padx=30, pady=30)

        container = ctk.CTkFrame(wrapper, fg_color="white", corner_radius=20)
        container.pack(fill="both", expand=True)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=2)
        container.grid_rowconfigure(0, weight=1)

        # LEFT PANEL - Deep blue
        left = ctk.CTkFrame(container, fg_color="#1E3A8A", corner_radius=20)
        left.grid(row=0, column=0, sticky="nswe")

        user = self.app.current_user or {}

        image_path = user.get("photo_path") or user.get("image") or ""
        profile_img = None
        if image_path:
            try:
                path = image_path
                if not os.path.isabs(path):
                    path = os.path.join(IMAGES_ROOT, path)
                profile_img = load_pet_image(path, size=(180, 180))
            except Exception:
                profile_img = None

        img_holder = ctk.CTkFrame(left, width=200, height=200, fg_color="#0F1E4D", corner_radius=20)
        img_holder.pack(pady=40, padx=40)
        img_holder.pack_propagate(False)

        img_label = ctk.CTkLabel(img_holder, image=profile_img, text="No Image" if not profile_img else "")
        img_label.image = profile_img
        img_label.pack(expand=True)

        info_block = ctk.CTkFrame(left, fg_color="#1E3A8A")
        info_block.pack(pady=(0, 12))
        ctk.CTkLabel(
            info_block,
            text=user.get("name") or "Your Name",
            font=("Georgia", 20, "bold"),
            text_color="white",
        ).pack(anchor="center")
        ctk.CTkLabel(
            info_block,
            text=user.get("email") or "",
            font=("Georgia", 14),
            text_color="#dbeafe",
        ).pack(anchor="center", pady=(2, 0))
        phone_txt = user.get("phone") or user.get("phone_number") or ""
        if phone_txt:
            ctk.CTkLabel(
                info_block,
                text=phone_txt,
                font=("Georgia", 13),
                text_color="#cbd5f5",
            ).pack(anchor="center")
        age_txt = user.get("age")
        if age_txt not in (None, ""):
            ctk.CTkLabel(
                info_block,
                text=f"Age: {age_txt}",
                font=("Georgia", 13),
                text_color="#cbd5f5",
            ).pack(anchor="center")

        img_entry = ctk.CTkEntry(left, width=220, placeholder_text="Profile Image Path")
        img_entry.insert(0, image_path)
        img_entry.pack(pady=(10, 5))

        def browse_photo():
            path = filedialog.askopenfilename(
                title="Select profile image",
                filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp")]
            )
            if path:
                img_entry.delete(0, "end")
                img_entry.insert(0, path)

        def remove_photo():
            img_entry.delete(0, "end")

        btn_box = ctk.CTkFrame(left, fg_color="transparent")
        btn_box.pack(pady=10)
        ctk.CTkButton(btn_box, text="Browse", width=100, command=browse_photo).pack(side="left", padx=5)
        ctk.CTkButton(btn_box, text="Remove", width=100, fg_color="#D64545", hover_color="#B53030", command=remove_photo).pack(side="left", padx=5)

        # RIGHT PANEL - Light blue
        right = ctk.CTkFrame(container, fg_color="#E8F0FD", corner_radius=20)
        right.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(right, text="Account Information", font=("Georgia", 26, "bold"), text_color="#1E3A8A").pack(anchor="w", padx=40, pady=(30, 12))

        form = ctk.CTkScrollableFrame(right, fg_color="#E8F0FD")
        form.pack(fill="both", expand=True, padx=30, pady=(0, 10))
        form.grid_columnconfigure(0, weight=1)

        fields = [
            ("Full Name", user.get("name", "")),
            ("Age", user.get("age", "")),
            ("Email", user.get("email", "")),
            ("Phone Number", user.get("phone", "")),
            ("Birthdate (YYYY-MM-DD)", user.get("birthdate", "")),
            ("Facebook URL", user.get("facebook_url", "")),
            ("Instagram URL", user.get("instagram_url", "")),
        ]

        self.profile_entries = {}
        for label, value in fields:
            ctk.CTkLabel(form, text=label, font=("Georgia", 14), text_color="#1E3A8A").pack(anchor="w", padx=10, pady=(8, 0))
            entry = ctk.CTkEntry(form, width=350)
            entry.insert(0, "" if value is None else str(value))
            entry.pack(padx=10, pady=5)
            self.profile_entries[label] = entry

        def save_profile():
            photo_path = img_entry.get().strip()
            try:
                age_val = self.profile_entries["Age"].get().strip()
                if age_val:
                    try:
                        age_val = int(age_val)
                    except Exception:
                        messagebox.showerror("Error", "Age must be a number.")
                        return
                else:
                    age_val = user.get("age")

                updated = self.controller.update_admin_profile(
                    self._get_admin_id(),
                    self.profile_entries["Full Name"].get(),
                    age_val,
                    self.profile_entries["Email"].get(),
                    self.profile_entries["Phone Number"].get(),
                    self.profile_entries["Birthdate (YYYY-MM-DD)"].get(),
                    photo_path,
                    self.profile_entries["Facebook URL"].get().strip(),
                    self.profile_entries["Instagram URL"].get().strip(),
                    current_password=(self.app.current_user or {}).get("password", ""),
                )
                if updated:
                    current = self.app.current_user or {}
                    current.update(updated)
                    self.app.current_user = current
                messagebox.showinfo("Saved", "Profile updated!")
                self.show_profile()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        actions = ctk.CTkFrame(right, fg_color="#E8F0FD")
        actions.pack(side="bottom", fill="x", padx=30, pady=(8, 16))
        # Bottom-right aligned actions
        ctk.CTkButton(actions, text="Save Profile", fg_color="#1E40AF", hover_color="#1E3A8A", width=180, height=40, command=save_profile).pack(side="right", padx=(0, 8), pady=4)

        def delete_account():
            if not messagebox.askyesno("Delete Account", "Delete this admin account?"):
                return
            try:
                self.controller.delete_admin_account(self._get_admin_id(), user.get("photo_path") or user.get("image") or "")
                messagebox.showinfo("Deleted", "Admin account deleted.")
                self.app.logout()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(actions, text="Delete Account", fg_color="#D64545", hover_color="#B53030", width=180, height=40, command=delete_account).pack(side="right", padx=(0, 8), pady=4)

    # =============================================================
    # 7. HELP CENTER
    # =============================================================
    def show_help_center(self):
        self.clear()
        hero = ctk.CTkFrame(self.content, fg_color="#00156A")
        hero.pack(fill="both", expand=True)

        ctk.CTkLabel(hero, text="Help Center", font=("Georgia", 44, "bold"), text_color="white").pack(
            pady=(22, 6)
        )
        ctk.CTkLabel(hero, text="Find answers, guides, and support information below.", font=("Georgia", 16),
                     text_color="#D4FAFF").pack(pady=(0, 18))

        shell = ctk.CTkFrame(hero, width=1100, height=640, corner_radius=40, fg_color="#D4FAFF", border_width=2, border_color="#9EC9FF")
        shell.pack(fill="both", expand=True, padx=22, pady=(0, 26))
        shell.pack_propagate(False)

        layout = ctk.CTkFrame(shell, fg_color="#D4FAFF")
        layout.pack(fill="both", expand=True, padx=26, pady=22)

        nav = ctk.CTkFrame(layout, fg_color="white", corner_radius=25, width=260, height=400)
        nav.pack(side="left", fill="y", padx=(0, 22))
        nav.pack_propagate(False)

        ctk.CTkLabel(nav, text="Categories", font=("Georgia", 22, "bold"), text_color="#06215A").pack(
            pady=(25, 15)
        )

        def help_btn(text, action):
            return ctk.CTkButton(
                nav,
                text=text,
                width=200,
                height=45,
                fg_color="#1E63D1",
                hover_color="#174DA6",
                corner_radius=12,
                font=("Georgia", 15),
                command=action,
            )

        content_card = ctk.CTkFrame(layout, fg_color="white", corner_radius=25)
        content_card.pack(side="left", fill="both", expand=True)

        output = ctk.CTkTextbox(content_card, fg_color="white", text_color="black", font=("Georgia", 14), wrap="word")
        output.pack(fill="both", expand=True, padx=25, pady=25)

        def load(text):
            output.delete("0.0", "end")
            output.insert("0.0", text)

        help_btn("FAQ", lambda: load(self.help_faq())).pack(pady=8)
        help_btn("Terms & Conditions", lambda: load(self.help_terms())).pack(pady=8)
        help_btn("Privacy Policy", lambda: load(self.help_privacy())).pack(pady=8)

        load(self.help_faq())

    def help_faq(self):
        return (
            "Adopter FAQ\n\n"
            "Q: How do I start the adoption process?\n"
            "A: Go to the Available Pets section, choose a pet you're interested in, and click the 'Apply for Adoption' button.\n\n"
            "Q: Do I need an account to adopt a pet?\n"
            "A: Yes. You must log in or create an adopter account before submitting any adoption request.\n\n"
            "Q: What information do I need to provide when applying?\n"
            "A: You are required to fill out your name, address, contact number, birthdate, and your previous adoption experience.\n\n"
            "Q: What happens after I submit my adoption request?\n"
            "A: Your request will be reviewed by an administrator. You will receive a notification once your request is approved or declined.\n\n"
            "Q: How long does it take for approval?\n"
            "A: Processing time varies depending on the number of requests and the admin’s evaluation. Most requests are reviewed within 1–3 days.\n\n"
            "Q: Why was my request declined?\n"
            "A: Decline reasons vary. Some admins include a specific reason. Common reasons include incomplete information, unsuitable environment, or conflicts with pet requirements.\n\n"
            "Q: Can I cancel my adoption request?\n"
            "A: Yes. You can cancel your request anytime as long as it is still marked as 'Pending'. Once approved, cancellation may no longer be allowed.\n\n"
            "Q: Where can I see my submitted requests?\n"
            "A: Go to the 'My Requests' page located in your menu. All your pending, approved, and declined requests are displayed there.\n\n"
            "Q: How do I know if my request was approved?\n"
            "A: You will receive an in-app notification. You may also check your request status under the 'My Requests' page.\n\n"
            "Q: Can I edit my personal information?\n"
            "A: Yes. Go to your 'Profile' page to update your name, phone number, birthdate, address, or adoption experience details.\n\n"
            "Q: What should I do after my request is approved?\n"
            "A: The admin will contact you for the next steps, including meeting schedules, requirements, or pet pickup arrangements.\n\n"
            "Q: Will my personal information be safe?\n"
            "A: Yes. All information is securely stored in our system and used only for adoption-related purposes.\n\n"
            "Q: Who can I contact for further help?\n"
            "A: You may use the 'Help & Support' section or message the admin directly if available in your app.\n"
        )

    def help_terms(self):
        return (
            "Terms & Conditions\n\n"
            "Welcome to FurEver Home. By continuing to use this system, all administrators acknowledge and "
            "agree to follow the guidelines governing the management of adopter data, pet records, adoption "
            "requests, notifications, and system operations. These terms ensure transparency, safety, and "
            "ethical use of the platform.\n\n"

            "1. Accuracy of Information\n"
            "Administrators are responsible for ensuring all data entered into the system—including pet details, "
            "adopter profiles, medical information, and adoption histories—is complete and accurate. Any outdated "
            "or incorrect information must be corrected immediately to avoid confusion and misuse.\n\n"

            "2. Proper Screening of Adoption Requests\n"
            "Admins must carefully evaluate every adoption request before approving or declining it. Evaluations "
            "should consider the adopter’s experience, readiness, living conditions, and the pet’s needs. Decisions "
            "must always prioritize the welfare, safety, and compatibility of the pet and adopter.\n\n"

            "3. Responsible Use of Administrative Privileges\n"
            "Admin access is a privilege and must not be used to alter, hide, destroy, or manipulate records for "
            "personal reasons. All actions taken inside the system must be legitimate, transparent, and aligned with "
            "official procedures. Unauthorized modification of adoption outcomes, pet availability, or system "
            "permissions is strictly prohibited.\n\n"

            "4. Data Privacy and Confidentiality\n"
            "Adopter information—including contact details, address, birthdate, and adoption history—is confidential "
            "and must be protected at all times. These details may only be used for adoption-related purposes and may "
            "not be disclosed or shared without proper consent. Admins are expected to follow basic data privacy "
            "protocols to prevent breaches and unauthorized access.\n\n"

            "5. Ethical Handling of Pet Records\n"
            "Pet profiles must accurately represent their true condition, behavior, medical status, and adoption "
            "availability. Misrepresenting age, breed, temperament, or health is not allowed. Pets marked as adopted "
            "must reflect real adoption status to avoid duplicate requests or misinformation.\n\n"

            "6. System Security and Account Protection\n"
            "Admins are responsible for safeguarding their login credentials. Passwords must not be shared with "
            "anyone under any circumstances. Any suspicious activity, unauthorized login attempts, or system "
            "irregularities must be reported immediately to maintain platform integrity.\n\n"

            "7. Integrity in Decision-Making\n"
            "All decisions made within the system—such as approving or rejecting adoption requests—must be fair, free "
            "from bias, and based solely on documented facts. Personal conflicts, favoritism, or discrimination must "
            "never influence administrative actions.\n\n"

            "8. Restrictions on Data Removal\n"
            "Admins may not remove pet profiles, adoption records, or user accounts unless authorized and justified. "
            "Deletion of important data for personal benefit or to conceal errors is strictly forbidden.\n\n"

            "9. Proper Communication and Feedback\n"
            "When declining adoption requests, admins are encouraged to provide clear, constructive, and respectful "
            "feedback so adopters understand the reason behind the decision. Communication must remain professional.\n\n"

            "10. System Updates and Features\n"
            "Admins must comply with any changes, updates, or new policies added to the system. System improvements "
            "may introduce new rules that administrators must adhere to.\n\n"

            "11. Accountability for Misuse\n"
            "Any abuse of administrative powers—such as unauthorized edits, tampering with records, or mishandling "
            "sensitive data—may result in revoked access, disciplinary action, or removal of admin privileges.\n\n"

            "12. Acceptance of Terms\n"
            "By using the FurEver Home system, administrators confirm they understand and accept all terms stated "
            "above. Continued system use implies ongoing agreement to these policies and future revisions.\n"
        )

    def help_privacy(self):
        return (
            "Privacy Policy\n\n"
            "This Privacy Policy describes how FurEver Home collects, uses, stores, and protects the "
            "personal information of both Adopters and Administrators who use the system.\n\n"
            "1. Information We Collect\n"
            "   • Adopter Information: name, address, email, phone number, birthdate, and adoption history.\n"
            "   • Admin Information: name, email, phone number, and profile details used for system management.\n"
            "   • System Activity: login records, request submissions, approval/decline actions.\n"
            "   • Pet Information: details added or updated by admins for adoption listings.\n\n"
            "2. How We Use Your Data\n"
            "The information collected is used solely for:\n"
            "   • Processing adoption requests\n"
            "   • Verifying adopter identity and readiness\n"
            "   • Sending notifications about request status updates\n"
            "   • Maintaining accurate adoption history\n"
            "   • Improving system performance and security\n"
            "   • Ensuring the safety and welfare of animals under the organization\n\n"
            "3. Storage & Security Measures\n"
            "   • All personal data is securely stored within the FurEver Home database.\n"
            "   • Access is restricted based on user role (Admin / Adopter).\n"
            "   • Passwords must be kept private and are not visible to staff.\n"
            "   • Security measures are applied to prevent unauthorized access, data leaks, and misuse.\n\n"
            "4. Information Sharing\n"
            "We do not sell or share any user data. Information may only be shared in the following cases:\n"
            "   • Adoption verification steps required by the organization\n"
            "   • Legal requests or compliance with authorities\n"
            "   • When adopter details are needed to finalize an adoption\n"
            "   • Internal record keeping for monitoring and transparency\n\n"
            "5. User Rights\n"
            "Users of the system have the right to:\n"
            "   • Request correction of incorrect or outdated information\n"
            "   • Review their submitted adoption details\n"
            "   • Receive updates regarding the status of their adoption requests\n"
            "   • Ask for clarification about how their data is used\n\n"
            "6. Data Retention\n"
            "   • Adoption records and related information are stored only as long as needed for system "
            "     operations and historical tracking.\n"
            "   • Inactive accounts or data may be archived but will remain protected.\n\n"
            "7. Protection of Minors\n"
            "FurEver Home may restrict adoption activities for minors. Personal data of users below the "
            "required age will not be collected without proper verification.\n\n"
            "8. Consent\n"
            "By using FurEver Home, users agree to the collection and use of their information as described "
            "in this Privacy Policy. Continued use of the system signifies acceptance of these practices.\n"
        )

    # =============================================================
    # 8. ABOUT US
    # =============================================================
    def show_about(self):
        self.clear()
        hero = ctk.CTkFrame(self.content, fg_color="#00156A")
        hero.pack(fill="both", expand=True)

        ctk.CTkLabel(hero, text="About Us", font=("Georgia", 44, "bold"), text_color="white").pack(
            pady=(22, 6)
        )
        ctk.CTkLabel(hero, text="Meet the team behind FurEver Home.", font=("Georgia", 16), text_color="#D4FAFF").pack(
            pady=(0, 18)
        )

        shell = ctk.CTkFrame(hero, width=1100, height=640, corner_radius=40, fg_color="#D4FAFF", border_width=2, border_color="#9EC9FF")
        shell.pack(fill="both", expand=True, padx=22, pady=(0, 26))
        shell.pack_propagate(False)

        scroll = ctk.CTkScrollableFrame(shell, fg_color="#D4FAFF", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=30, pady=20)

        admins_card = ctk.CTkFrame(scroll, fg_color="white", corner_radius=25)
        admins_card.pack(fill="x", pady=20)

        ctk.CTkLabel(admins_card, text="Our Admins", font=("Georgia", 26, "bold"), text_color="#06215A").pack(
            anchor="w", padx=25, pady=(20, 10)
        )

        try:
            admins = self.controller.admin_profiles()
        except Exception:
            admins = []

        if not hasattr(self, "fb_icon"):
            self.fb_icon = self._load_icon("fb.png", size=(22, 22))
        if not hasattr(self, "ig_icon"):
            self.ig_icon = self._load_icon("ig.png", size=(22, 22))

        base_dir = PROJECT_ROOT
        images_dir = IMAGES_ROOT

        def load_photo(path_value, size=(70, 70)):
            if not path_value:
                return None
            candidates = []
            if os.path.isabs(path_value):
                candidates.append(path_value)
            else:
                candidates.append(os.path.join(images_dir, path_value))
                candidates.append(os.path.join(base_dir, path_value))
            for path in candidates:
                if not os.path.exists(path):
                    continue
                try:
                    img = Image.open(path).convert("RGBA")
                    return ctk.CTkImage(img, size=size)
                except Exception:
                    continue
            return None

        fallback_photos = {
            "Angelica C. Corpuz": load_photo("angelica.jpg"),
            "Ronin Jacob C. Guevarra": load_photo("ronin.jpg"),
            "Francine Anne M. Villaraza": load_photo("francine.jpg"),
        }

        icon_map = {
            "fb": self.fb_icon,
            "facebook": self.fb_icon,
            "ig": self.ig_icon,
            "instagram": self.ig_icon,
        }

        def add_link(parent, icon, text, url):
            row = ctk.CTkFrame(parent, fg_color="#f2f5fa")
            row.pack(anchor="w", padx=15, pady=2)
            if icon:
                icon_lbl = ctk.CTkLabel(row, image=icon, text="")
                icon_lbl.image = icon
                icon_lbl.pack(side="left", padx=(0, 6))
            link = ctk.CTkLabel(
                row,
                text=text,
                font=("Georgia", 13, "bold"),
                text_color="#0a3d91",
                cursor="hand2",
            )
            link.pack(side="left")
            link.bind("<Button-1>", lambda _e=None, u=url: webbrowser.open_new(u))

        if not admins:
            ctk.CTkLabel(admins_card, text="No admin profiles yet.", font=("Georgia", 14), text_color="#777").pack(
                padx=25, pady=(0, 14), anchor="w"
            )

        for admin in admins:
            entry = ctk.CTkFrame(admins_card, fg_color="#f2f5fa", corner_radius=15)
            entry.pack(fill="x", padx=25, pady=10)

            row = ctk.CTkFrame(entry, fg_color="#f2f5fa")
            row.pack(fill="x", padx=10, pady=6)

            name = admin.get("name") or "Unknown"
            links = []
            fb = admin.get("facebook_url") or admin.get("facebook")
            ig = admin.get("instagram_url") or admin.get("instagram")
            if fb:
                links.append(("Facebook", fb, "fb"))
            if ig:
                links.append(("Instagram", ig, "ig"))

            photo = load_photo(admin.get("photo_path")) or fallback_photos.get(name)
            if photo:
                img_lbl = ctk.CTkLabel(row, image=photo, text="")
                img_lbl.image = photo
                img_lbl.pack(side="left", padx=(4, 12), pady=6)

            content = ctk.CTkFrame(row, fg_color="#f2f5fa")
            content.pack(side="left", fill="both", expand=True)

            ctk.CTkLabel(content, text=name, font=("Georgia", 17, "bold"), text_color="#06215A").pack(
                anchor="w", pady=(0, 4)
            )
            for label, url, icon_key in links:
                if not url:
                    continue
                add_link(content, icon_map.get((icon_key or "").lower()), label, url)

        about_card = ctk.CTkFrame(scroll, fg_color="white", corner_radius=25)
        about_card.pack(fill="x", pady=20)

        if not hasattr(self, "about_logo"):
            self.about_logo = self._load_icon("FurEver_Home_Logo.png", size=(80, 80))
        header_row = ctk.CTkFrame(about_card, fg_color="white")
        header_row.pack(fill="x", padx=18, pady=(18, 8))
        if self.about_logo:
            logo_lbl = ctk.CTkLabel(header_row, image=self.about_logo, text="")
            logo_lbl.image = self.about_logo
            logo_lbl.pack(side="left", padx=(6, 14))
        ctk.CTkLabel(header_row, text="About FurEver Home", font=("Georgia", 24, "bold"), text_color="#06215A").pack(
            side="left", pady=4
        )

        about_text = (
            "FurEver Home is a community-driven pet adoption platform designed to make the adoption process simple, "
            "transparent, and accessible for everyone. Our system connects loving adopters with pets in need of safe and permanent homes.\n\n"
            "Through our platform, adopters can browse available pets, submit applications, track their status, and receive "
            "updates directly from our administrators.\n\n"
            "FurEver Home helps shelters promote responsible pet ownership and ensures every pet finds the family they deserve. "
            "If you have questions or concerns, feel free to reach out to our administrators.\n\n"
            "Together, we can give every pet a chance at a FurEver Home."
        )

        ctk.CTkLabel(
            about_card,
            text=about_text,
            font=("Georgia", 18),
            text_color="#444",
            justify="center",
            wraplength=850,
        ).pack(anchor="center", padx=40, pady=(0, 22))
