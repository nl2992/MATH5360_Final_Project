"""
Assemble the final MATH GR5360 PowerPoint deck.

Strategy:
* Start from the case-comp template the team already populated
  (`5360-Presentation.pptx`): keep its title slide, the diagnostic
  slides we already filled in, the strategy/walk-forward sections,
  and the contract-specs panel — that's slides 1 through 17.
* Replace the two "XXX INSERT" diagnostic slides (14 & 15) with our
  Columbia-themed VR and Push–Response figures.
* Drop everything from slide 18 onwards (Atlas Advisory case-comp
  boilerplate that snuck through from the original template).
* Append new clean slides built around the Columbia-themed figures
  in `report/presentation/figures/` and `report/figures/`, plus
  bullet text refined from the placeholder deck `TY_BTC_Channel_WDC_1.pptx`
  but updated to the FINAL parity-checked numbers from
  `results/walkforward/`.

Output: `report/presentation/MATH5360_Final_Group1.pptx`
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

# -----------------------------------------------------------------------------
# Palette (must match the Columbia theme used in the figures)
# -----------------------------------------------------------------------------
COL_NAVY = RGBColor(0x01, 0x21, 0x69)
COL_BLUE = RGBColor(0xB9, 0xD9, 0xEB)
COL_INK = RGBColor(0x1B, 0x36, 0x5D)
COL_GOLD = RGBColor(0xA2, 0x8D, 0x5B)
COL_RED = RGBColor(0xA0, 0x30, 0x33)
COL_GREEN = RGBColor(0x3F, 0x6F, 0x4A)
COL_GREY = RGBColor(0x9A, 0xA1, 0xA9)
COL_LIGHT = RGBColor(0xE6, 0xE9, 0xEE)
COL_CHARCOAL = RGBColor(0x2A, 0x2A, 0x2A)
COL_CREAM = RGBColor(0xF4, 0xF1, 0xEA)

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = Path("/Users/nigelli/Downloads/5360-Presentation.pptx")
FIG_PRES = ROOT / "report" / "presentation" / "figures"
FIG_REPORT = ROOT / "report" / "figures"
OUT = ROOT / "report" / "presentation" / "MATH5360_Final_Group1.pptx"


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def remove_slides_after(prs: Presentation, keep_count: int) -> None:
    """Delete slides past the first `keep_count` from the deck."""
    sldIdLst = prs.slides._sldIdLst  # noqa: SLF001
    parts = list(sldIdLst)
    to_remove = parts[keep_count:]
    for sldId in to_remove:
        rId = sldId.get(qn("r:id"))
        prs.part.drop_rel(rId)
        sldIdLst.remove(sldId)


def add_blank_slide(prs: Presentation):
    """Add a slide using the 'Blank' or 'Title Only' layout."""
    layout = prs.slide_layouts[3]  # 'Title Only'
    return prs.slides.add_slide(layout)


def paint_background(slide, color: RGBColor) -> None:
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_textbox(
    slide,
    left,
    top,
    width,
    height,
    text: str,
    *,
    size: float = 12,
    bold: bool = False,
    color: RGBColor = COL_INK,
    align=PP_ALIGN.LEFT,
    font_family: str = "Calibri",
):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.name = font_family
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color
    return box


def add_bullets(slide, left, top, width, height, items, *, size: float = 12,
                color: RGBColor = COL_INK, bullet_char: str = "•"):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    for i, line in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        r = p.add_run()
        r.text = f"{bullet_char}  {line}"
        r.font.size = Pt(size)
        r.font.color.rgb = color
        r.font.name = "Calibri"
    return box


def add_title_strip(slide, title: str, section: str = ""):
    """Top-of-slide title strip in the Columbia palette."""
    sw = slide.part.package.presentation_part.presentation.slide_width
    # Title bar
    title_box = slide.shapes.add_textbox(Inches(0.4), Inches(0.25), sw - Inches(0.8), Inches(0.55))
    tf = title_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = title
    r.font.name = "Calibri"
    r.font.size = Pt(24)
    r.font.bold = True
    r.font.color.rgb = COL_NAVY
    # Subtle divider
    from pptx.shapes.connector import Connector  # noqa: F401  (ensure import)
    line = slide.shapes.add_connector(1, Inches(0.4), Inches(0.85), sw - Inches(0.4), Inches(0.85))
    line.line.color.rgb = COL_NAVY
    line.line.width = Pt(1.0)
    # Section tag
    if section:
        section_box = slide.shapes.add_textbox(sw - Inches(2.6), Inches(0.25), Inches(2.2), Inches(0.4))
        tf2 = section_box.text_frame
        p2 = tf2.paragraphs[0]
        p2.alignment = PP_ALIGN.RIGHT
        r2 = p2.add_run()
        r2.text = section.upper()
        r2.font.name = "Calibri"
        r2.font.size = Pt(10)
        r2.font.bold = True
        r2.font.color.rgb = COL_GOLD


def add_footer(slide, slide_no: int, total: int):
    sw = slide.part.package.presentation_part.presentation.slide_width
    sh = slide.part.package.presentation_part.presentation.slide_height
    box = slide.shapes.add_textbox(Inches(0.4), sh - Inches(0.45), sw - Inches(0.8), Inches(0.3))
    tf = box.text_frame
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = f"MATH GR5360 Final Project · Group 1 · Columbia MAFN — Spring 2026"
    r.font.size = Pt(9)
    r.font.color.rgb = COL_GREY
    r.font.name = "Calibri"
    p.alignment = PP_ALIGN.LEFT
    box2 = slide.shapes.add_textbox(sw - Inches(1.4), sh - Inches(0.45), Inches(1.0), Inches(0.3))
    tf2 = box2.text_frame
    p2 = tf2.paragraphs[0]
    p2.alignment = PP_ALIGN.RIGHT
    r2 = p2.add_run()
    r2.text = f"{slide_no} / {total}"
    r2.font.size = Pt(9)
    r2.font.color.rgb = COL_GREY
    r2.font.name = "Calibri"


def insert_image(slide, path: Path, left, top, width=None, height=None):
    if not path.exists():
        print(f"[warn] missing image: {path}")
        return None
    return slide.shapes.add_picture(str(path), left, top, width=width, height=height)


def fit_image_in_box(slide, path: Path, box_left, box_top, box_w, box_h):
    """Insert an image fit inside a box, preserving aspect ratio and centring."""
    if not path.exists():
        print(f"[warn] missing image: {path}")
        return None
    pic = slide.shapes.add_picture(str(path), box_left, box_top)
    iw, ih = pic.width, pic.height
    scale = min(box_w / iw, box_h / ih)
    nw = int(iw * scale)
    nh = int(ih * scale)
    pic.width = nw
    pic.height = nh
    pic.left = int(box_left + (box_w - nw) / 2)
    pic.top = int(box_top + (box_h - nh) / 2)
    return pic


# -----------------------------------------------------------------------------
# Slide builders
# -----------------------------------------------------------------------------
def build_image_slide(prs: Presentation, *, title: str, section: str,
                      image: Path, caption: str, slide_no: int, total: int,
                      side_bullets: list[str] | None = None):
    slide = add_blank_slide(prs)
    paint_background(slide, RGBColor(0xFF, 0xFF, 0xFF))
    add_title_strip(slide, title, section)
    sw, sh = prs.slide_width, prs.slide_height
    # Image takes most of the left/centre. Bullets on the right if any.
    if side_bullets:
        img_box_w = int(sw * 0.62)
        fit_image_in_box(slide, image, Inches(0.4), Inches(1.0), img_box_w, sh - Inches(2.0))
        # Bullets on right
        right_x = Inches(0.4) + img_box_w + Inches(0.2)
        right_w = sw - right_x - Inches(0.4)
        add_bullets(slide, right_x, Inches(1.1), right_w, sh - Inches(2.2), side_bullets, size=11)
    else:
        fit_image_in_box(slide, image, Inches(0.4), Inches(1.0), sw - Inches(0.8), sh - Inches(2.0))
    # Caption strip
    add_textbox(slide, Inches(0.4), sh - Inches(0.95), sw - Inches(0.8), Inches(0.45),
                caption, size=10.5, color=COL_INK)
    add_footer(slide, slide_no, total)


def build_metrics_table_slide(prs: Presentation, slide_no: int, total: int):
    slide = add_blank_slide(prs)
    paint_background(slide, RGBColor(0xFF, 0xFF, 0xFF))
    add_title_strip(slide, "Performance Metrics", section="Results")
    sw, sh = prs.slide_width, prs.slide_height
    fit_image_in_box(slide, FIG_PRES / "slide_01_performance_metrics.png",
                     Inches(0.4), Inches(1.0), sw - Inches(0.8), sh - Inches(2.0))
    add_textbox(slide, Inches(0.4), sh - Inches(0.95), sw - Inches(0.8), Inches(0.45),
                "Both markets earn ~4× Return on Account out-of-sample. TY's signal is slow and "
                "low-vol; BTC's is fast and high-vol — the same Channel WithDDControl framework "
                "calibrates to each market's autocorrelation structure via walk-forward optimisation.",
                size=10.5, color=COL_INK)
    add_footer(slide, slide_no, total)


def build_section_divider(prs: Presentation, *, label: str, big: str, slide_no: int, total: int):
    slide = add_blank_slide(prs)
    paint_background(slide, COL_NAVY)
    sw, sh = prs.slide_width, prs.slide_height
    # Label
    add_textbox(slide, Inches(0.6), Inches(2.6), sw - Inches(1.2), Inches(0.5),
                label.upper(), size=14, bold=True, color=COL_GOLD)
    # Big text
    add_textbox(slide, Inches(0.6), Inches(3.1), sw - Inches(1.2), Inches(2.0),
                big, size=36, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))
    # Footer in white
    box = slide.shapes.add_textbox(Inches(0.4), sh - Inches(0.45), sw - Inches(0.8), Inches(0.3))
    tf = box.text_frame
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = "MATH GR5360 Final Project · Group 1 · Columbia MAFN — Spring 2026"
    r.font.size = Pt(9)
    r.font.color.rgb = COL_LIGHT
    r.font.name = "Calibri"
    box2 = slide.shapes.add_textbox(sw - Inches(1.4), sh - Inches(0.45), Inches(1.0), Inches(0.3))
    tf2 = box2.text_frame
    p2 = tf2.paragraphs[0]
    p2.alignment = PP_ALIGN.RIGHT
    r2 = p2.add_run()
    r2.text = f"{slide_no} / {total}"
    r2.font.size = Pt(9)
    r2.font.color.rgb = COL_LIGHT
    r2.font.name = "Calibri"


def build_conclusion_slide(prs: Presentation, slide_no: int, total: int):
    slide = add_blank_slide(prs)
    paint_background(slide, RGBColor(0xFF, 0xFF, 0xFF))
    add_title_strip(slide, "Conclusion", section="Summary")
    sw, sh = prs.slide_width, prs.slide_height
    big_quote = ('"Trend-following is real in both markets — but the usable horizon is market-specific."')
    add_textbox(slide, Inches(0.6), Inches(1.1), sw - Inches(1.2), Inches(0.7),
                big_quote, size=18, bold=True, color=COL_NAVY, align=PP_ALIGN.LEFT)
    cards = [
        ("01",
         "Diagnostics",
         "Variance-ratio test and push–response confirm trend-following at the multi-week horizon "
         "for TY (Spearman ρ ≈ 0.59 at 18 sessions) and at the multi-day horizon for BTC "
         "(ρ ≈ 0.67 at 12 days). Same statistical framework — different frequency bands."),
        ("02",
         "Strategy",
         "Channel WithDDControl ported from main.m / ezread.m to Python (Numba JIT) and C++17. "
         "Walk-forward 4-yr IS / 1-Q OOS over the full ChnLen × StpPct grid, "
         "objective = Net Profit / Max Drawdown."),
        ("03",
         "OOS Results",
         "TY: $68 336 net / 4.31× RoA / Sharpe 0.31 over 1987–2026 (155 quarters). "
         "BTC: $536 397 net / 4.07× RoA / Sharpe 3.01 over 2023–2026 (7 quarters). "
         "Both deliver ≈ 4× return-on-account with full slippage charged."),
        ("04",
         "Robustness",
         "Python ↔ C++ parity to float-64 on every metric and every closed trade. "
         "T × τ sweep confirms the assignment-prescribed (4 yr, 1 Q) is the well-behaved choice. "
         "1-minute resolution earns marginally more (RoA 4.61×) but does not change the picture."),
    ]
    card_y = Inches(2.0)
    card_h = Inches(1.0)
    for i, (num, head, body) in enumerate(cards):
        y = card_y + i * (card_h + Inches(0.05))
        # number
        nb = slide.shapes.add_textbox(Inches(0.6), y, Inches(0.7), card_h)
        tf = nb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        r = p.add_run()
        r.text = num
        r.font.size = Pt(28)
        r.font.bold = True
        r.font.color.rgb = COL_GOLD
        r.font.name = "Calibri"
        # Heading
        hb = slide.shapes.add_textbox(Inches(1.4), y, Inches(2.1), Inches(0.4))
        tfh = hb.text_frame
        ph = tfh.paragraphs[0]
        rh = ph.add_run()
        rh.text = head
        rh.font.size = Pt(13)
        rh.font.bold = True
        rh.font.color.rgb = COL_NAVY
        rh.font.name = "Calibri"
        # Body
        bb = slide.shapes.add_textbox(Inches(3.6), y, sw - Inches(4.0), card_h)
        tfb = bb.text_frame
        tfb.word_wrap = True
        pb = tfb.paragraphs[0]
        rb = pb.add_run()
        rb.text = body
        rb.font.size = Pt(10.5)
        rb.font.color.rgb = COL_INK
        rb.font.name = "Calibri"
    add_footer(slide, slide_no, total)


def build_appendix_slide(prs: Presentation, slide_no: int, total: int):
    slide = add_blank_slide(prs)
    paint_background(slide, RGBColor(0xFF, 0xFF, 0xFF))
    add_title_strip(slide, "Appendix — repository, parity table, key figures", section="Appendix")
    sw, sh = prs.slide_width, prs.slide_height
    items = [
        "Repository: github.com/nl2992/MATH5360_Final_Project",
        "Walk-forward Python artifacts: results/walkforward/{TY_5m, BTC_5m, TY_1m}/",
        "C++ parity artifacts: results/cpp_parity/{TY, BTC}/",
        "Diagnostics (VR + Push–Response cached tables): results/diagnostics/",
        "Comprehensive write-up: report/FINAL_REPORT.md",
        "Slide-companion narrative: report/presentation/demo.md",
        "All figures regenerated by: python scripts/build_final_report_figures.py "
        "and scripts/build_presentation_figures.py",
        "Python ↔ C++ parity: every metric and every closed trade match to float-64 — "
        "see results/walkforward/python_cpp_fidelity_comparison.csv",
    ]
    add_bullets(slide, Inches(0.6), Inches(1.2), sw - Inches(1.2), sh - Inches(2.0), items, size=12)
    add_textbox(slide, Inches(0.6), sh - Inches(1.0), sw - Inches(1.2), Inches(0.5),
                "Channel WithDDControl ported from main.m / ezread.m. Python core JIT-compiled with Numba; "
                "C++17 reference engine confirms parity to float-64.",
                size=10, color=COL_GREY)
    add_footer(slide, slide_no, total)


# -----------------------------------------------------------------------------
# Slides 14 & 15 — drop "XXX INSERT" and replace with our diagnostic figures
# -----------------------------------------------------------------------------
def replace_slide_with_image(prs: Presentation, slide_index: int, *, title: str,
                             image: Path, caption: str, section: str, slide_no: int, total: int):
    """Wipe the contents of a template slide and re-populate with our content."""
    slide = prs.slides[slide_index]
    # Remove every shape
    for shape in list(slide.shapes):
        sp = shape._element  # noqa: SLF001
        sp.getparent().remove(sp)
    # Repaint
    paint_background(slide, RGBColor(0xFF, 0xFF, 0xFF))
    add_title_strip(slide, title, section)
    sw, sh = prs.slide_width, prs.slide_height
    fit_image_in_box(slide, image, Inches(0.4), Inches(1.0), sw - Inches(0.8), sh - Inches(2.0))
    add_textbox(slide, Inches(0.4), sh - Inches(0.95), sw - Inches(0.8), Inches(0.45),
                caption, size=10.5, color=COL_INK)
    add_footer(slide, slide_no, total)


# -----------------------------------------------------------------------------
# Driver
# -----------------------------------------------------------------------------
def main() -> None:
    prs = Presentation(str(TEMPLATE))

    # Step 1 — drop slides 18-59 (Atlas Advisory leftovers).
    print(f"start: {len(prs.slides)} slides")
    remove_slides_after(prs, keep_count=17)
    print(f"after trim: {len(prs.slides)} slides (kept 1-17 from template)")

    # We now have 17 template slides. We will add 18 more.
    # Total final slide count for footer numbering:
    TOTAL = 35

    # Update the title slide author/section text? Leave as-is per the user.

    # Step 2 — replace slide 14 ("Evidence: Autocorrelation Structure")
    replace_slide_with_image(
        prs, 13,
        title="Evidence — Variance Ratio Profile (TY vs BTC)",
        image=FIG_REPORT / "fig_vr_curves.png",
        caption=(
            "Lo–MacKinlay VR(q) on price differences, log-spaced horizons. "
            "TY hovers just below 1 across all q (random-walk-like, dipping ~0.89 at 10 sessions). "
            "BTC reaches a deeper 0.82 at ~8.6 days. Neither rejects the null at 5%, but the push–response "
            "test on the next slide tells the actually informative story for our strategy."
        ),
        section="Diagnostics", slide_no=14, total=TOTAL,
    )

    # Step 3 — replace slide 15 ("Evidence: Variance Ratio Recovery")
    replace_slide_with_image(
        prs, 14,
        title="Evidence — Push–Response Diagrams",
        image=FIG_REPORT / "fig_push_response.png",
        caption=(
            "Conditional mean of the forward response per push-decile, with bin-level standard errors. "
            "TY shows positive Spearman ρ ≈ 0.59 (p ≈ 0.06) at 1440 bars (~18 sessions) — multi-week trend. "
            "BTC shows ρ ≈ +0.67 (p ≈ 0.02) at 3456 bars (~12 days). Mean-reverting at shorter horizons. "
            "These horizons drive the walk-forward picks of L*."
        ),
        section="Diagnostics", slide_no=15, total=TOTAL,
    )

    # Step 4 — append new content slides starting from S18
    next_no = 18

    # 18 — section divider for Performance
    build_section_divider(prs,
                          label="Out-of-Sample Performance",
                          big="Walk-forward results for both markets",
                          slide_no=next_no, total=TOTAL)
    next_no += 1

    # 19 — performance metrics Bloomberg-style table
    build_metrics_table_slide(prs, slide_no=next_no, total=TOTAL)
    next_no += 1

    # 20 — TY equity + position
    build_image_slide(
        prs,
        title="TY — out-of-sample equity & portfolio position",
        section="Primary Market — TY",
        image=FIG_PRES / "slide_02_ty_equity_position.png",
        caption=(
            "Channel WithDDControl on TY (10-yr Treasury futures) over 1987-06 → 2026-03 — "
            "155 quarterly walk-forward windows stitched, $100k initial equity. "
            "Net OOS profit $68 336 / Max DD $15 865 / Return on Account 4.31× / Sharpe 0.31 / 395 trades. "
            "Position panel shows long/short/flat state at bar resolution."
        ),
        slide_no=next_no, total=TOTAL,
    )
    next_no += 1

    # 21 — TY drawdown
    build_image_slide(
        prs,
        title="TY — Chekhlov drawdown family",
        section="Primary Market — TY",
        image=FIG_PRES / "slide_03_ty_drawdown_family.png",
        caption=(
            "Top: % off running peak. Bottom: $ off running peak. Max DD ≈ 11% / $15.9k. "
            "CDD(α=0.05) ≈ $13.3k indicates the worst 5% of drawdown bars are concentrated near the max. "
            "Long underwater stretches are structural for a 1.5%/yr trend-following bond strategy."
        ),
        slide_no=next_no, total=TOTAL,
    )
    next_no += 1

    # 22 — TY trade distribution
    build_image_slide(
        prs,
        title="TY — out-of-sample trade PnL distribution",
        section="Primary Market — TY",
        image=FIG_PRES / "slide_04_ty_trade_distribution.png",
        caption=(
            "Win rate 33% but average winner $1 265 vs average loser −$897 — classic right-skewed "
            "breakout payoff. Profit factor 0.70 because the system loses small and wins large; "
            "the assignment-mandated Net P / Max DD objective is what we optimise against (4.31×)."
        ),
        slide_no=next_no, total=TOTAL,
    )
    next_no += 1

    # 23 — TY best trade
    build_image_slide(
        prs,
        title="TY — most profitable OOS trade (autopsy)",
        section="Primary Market — TY",
        image=FIG_PRES / "slide_05_ty_best_trade.png",
        caption=(
            "21 Jan 2020 LONG 129.56 → 137.75 over 50 days (+$8 170). "
            "Channel breakout above the 1 920-bar high right as COVID drove a flight-to-safety bond rally. "
            "Trailing-equity stop fired after the initial impulse decayed — textbook trend payoff."
        ),
        slide_no=next_no, total=TOTAL,
    )
    next_no += 1

    # 24 — TY worst trade — why it got cooked
    build_image_slide(
        prs,
        title="TY — worst OOS trade · why it got cooked",
        section="Primary Market — TY",
        image=FIG_PRES / "slide_06_ty_worst_trade.png",
        side_bullets=[
            "22 Feb 2002 LONG @ 107.38 — broke above the 3 200-bar (~40-day) high.",
            "Treasuries reversed almost immediately on hawkish-Fed signals at the late-Feb FOMC.",
            "Price slid 2.93 pts in 12 days; trailing stop fired at $-2 952.",
            "Classic 'breakout caught at the local top' before mean-reversion fired.",
            "Wide L = 3 200 channel made the per-bar stop physically distant — loss compounded before exit.",
            "The push–response diagnostic for short horizons is near zero; some breakouts get faded.",
        ],
        caption="Source: Group 1 walk-forward (TF Data 5-min OHLC, $100k initial equity)",
        slide_no=next_no, total=TOTAL,
    )
    next_no += 1

    # 25 — TY parameter stability
    build_image_slide(
        prs,
        title="TY — walk-forward parameter stability",
        section="Primary Market — TY",
        image=FIG_PRES / "slide_07_ty_param_stability.png",
        caption=(
            "Channel length L converges to a tight cluster around 1 920 bars (≈ 24 trading days). "
            "Drawdown stop S almost always at 1% of running equity. Optimiser does not flip wildly — "
            "the chosen objective (Net Profit / Max Drawdown) is well-behaved on TY."
        ),
        slide_no=next_no, total=TOTAL,
    )
    next_no += 1

    # 26 — section divider for BTC
    build_section_divider(prs,
                          label="Secondary Market — BTC",
                          big="Same framework, faster horizon",
                          slide_no=next_no, total=TOTAL)
    next_no += 1

    # 27 — BTC equity + position
    build_image_slide(
        prs,
        title="BTC — out-of-sample equity & portfolio position",
        section="Secondary Market — BTC",
        image=FIG_PRES / "slide_02_btc_equity_position.png",
        caption=(
            "Channel WithDDControl on BTC (CME Bitcoin futures) over 2023-08 → 2026-02 — 7 quarterly "
            "OOS windows. Net OOS profit $536 397 / Max DD $131 729 / Return on Account 4.07× / "
            "Sharpe 3.01 / 1 094 trades. Equity grows from $100k to $636k driven by the 2024-25 cycle."
        ),
        slide_no=next_no, total=TOTAL,
    )
    next_no += 1

    # 28 — BTC drawdown
    build_image_slide(
        prs,
        title="BTC — Chekhlov drawdown family",
        section="Secondary Market — BTC",
        image=FIG_PRES / "slide_03_btc_drawdown_family.png",
        caption=(
            "Max DD ≈ 22% / $131.7k. Recovery is fast — most underwater stretches are weeks, not "
            "months. CDD(α=0.05) ≈ $111.8k. Larger absolute dollar swings than TY, but realised "
            "vol is ~8× higher so the % drawdown footprint is comparable."
        ),
        slide_no=next_no, total=TOTAL,
    )
    next_no += 1

    # 29 — BTC trade distribution
    build_image_slide(
        prs,
        title="BTC — out-of-sample trade PnL distribution",
        section="Secondary Market — BTC",
        image=FIG_PRES / "slide_04_btc_trade_distribution.png",
        caption=(
            "Win rate 42% with average winner $4 327 vs average loser −$2 285 — same right-skew as TY "
            "but with a higher hit rate. Profit factor 1.37. The intraday push–response is positive "
            "at the right horizons, supporting the higher hit rate."
        ),
        slide_no=next_no, total=TOTAL,
    )
    next_no += 1

    # 30 — BTC best trade
    build_image_slide(
        prs,
        title="BTC — most profitable OOS trade (autopsy)",
        section="Secondary Market — BTC",
        image=FIG_PRES / "slide_05_btc_best_trade.png",
        caption=(
            "02 Mar 2025 LONG 85 720 → 94 748 in 25 minutes (+$45 115). "
            "Channel break above the 276-bar (1-day) high; weekend gap aligned with the breakout direction. "
            "$9 028 price move × $5 BTC point value − $25 round-turn slippage = +$45 115 in 5 bars."
        ),
        slide_no=next_no, total=TOTAL,
    )
    next_no += 1

    # 31 — BTC worst trade — why it got cooked
    build_image_slide(
        prs,
        title="BTC — worst OOS trade · why it got cooked",
        section="Secondary Market — BTC",
        image=FIG_PRES / "slide_06_btc_worst_trade.png",
        side_bullets=[
            "22 Aug 2025 SHORT @ 112 075 — broke below the 276-bar (1-day) low.",
            "Within 90 minutes BTC pumped $2 115 (+1.9%) against the position.",
            "Tight 1% drawdown stop fired at the second bar after the move ($114 190).",
            "Channel breakout in BTC's mean-reverting 1-day regime — recurring failure mode.",
            "The push–response diagram already flagged BTC as mean-reverting at the 1-day horizon "
            "(Spearman ρ = −0.38).",
            "The −$10 600 loss is ≈ 8% of the OOS Max DD — paid once to stay in the longer-horizon trend regime.",
        ],
        caption="Source: Group 1 walk-forward (TF Data 5-min OHLC, $100k initial equity)",
        slide_no=next_no, total=TOTAL,
    )
    next_no += 1

    # 32 — BTC parameter stability
    build_image_slide(
        prs,
        title="BTC — walk-forward parameter stability",
        section="Secondary Market — BTC",
        image=FIG_PRES / "slide_07_btc_param_stability.png",
        caption=(
            "BTC has only 7 quarterly OOS windows (the sample's IS warmup eats ~4 years from inception). "
            "Optimiser cycles between L = 276 (1 day) in choppy regimes and L = 1 104 (4 days) in the "
            "late-2025 trend phase. S* fixed at 1%. Instability is structural — BTC's regime is shifting."
        ),
        slide_no=next_no, total=TOTAL,
    )
    next_no += 1

    # IS vs OOS decay
    build_image_slide(
        prs,
        title="In-sample vs out-of-sample decay",
        section="Robustness",
        image=FIG_REPORT / "fig_is_oos_metrics.png",
        caption=(
            "Sharpe decay: TY 0.41 → 0.31 (-24%); BTC 4.52 → 3.01 (-33%). "
            "Profit-per-quarter decay: TY 26%, BTC 130% (BTC's IS objective favoured smaller L which "
            "truncated the most explosive late-2024 trends — sample-specific, not a forward claim). "
            "Quarterly OOS hit rate: TY 54.8% (85/155), BTC 100% (7/7)."
        ),
        slide_no=next_no, total=TOTAL,
    )
    next_no += 1

    # Conclusion
    build_conclusion_slide(prs, slide_no=next_no, total=TOTAL)
    next_no += 1

    # Appendix
    build_appendix_slide(prs, slide_no=next_no, total=TOTAL)
    next_no += 1

    print(f"final: {len(prs.slides)} slides")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT))
    print(f"[ok] saved -> {OUT}")


if __name__ == "__main__":
    main()
