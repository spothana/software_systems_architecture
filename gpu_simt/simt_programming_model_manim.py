"""
simt_programming_model_manim.py  —  SIMT programming model with ManimGL
========================================================================
A conceptual explainer of the GPU programming model: hierarchically
decomposing a problem into threads / CTAs / grids, and scalably distributing
that work across whatever hardware happens to exist.

This is the THIRD film in the SIMT series and a FULLY SEPARATE render:
  - simt_programming_model_manim.py - the model: how you  carve a problem up.
  - simt_scheduling_manim.py - issue scheduling.
  - simt_divergence_manim.py — branch divergence.

Recommended viewing order: this film first (model), then scheduling,
then divergence (mechanism). Model before mechanism.

Chapters (one Scene each):

  Chapter 1 — FilmIntro          : title card
  Chapter 2 — ProblemScene       : why explicit parallelism doesn't scale
  Chapter 3 — DecompositionScene : problem -> grid / block / element
  Chapter 4 — HierarchyScene     : element->thread, block->CTA, grid->grid
  Chapter 5 — CooperationScene   : threads in a CTA share + synchronize
  Chapter 6 — StateScene         : per-group state — many configs, no drain
  Chapter 7 — ScalabilityScene   : core -> many cores -> many GPUs
  Chapter 8 — PayoffScene        : the model -> matrix multiply / AI

Install
-------
    pip install manimgl
    sudo apt install libpango1.0-dev ffmpeg
    sudo apt install espeak-ng        # optional, for --narrate

Run one scene
-------------
    manimgl simt_programming_model_manim.py DecompositionScene

Render one scene to 4K
----------------------
    manimgl simt_programming_model_manim.py ScalabilityScene -w --resolution 3840x2160

Render the whole film
---------------------
    python simt_programming_model_manim.py --all
    python simt_programming_model_manim.py --all --resolution 1920x1080
    python simt_programming_model_manim.py --all --narrate
    python simt_programming_model_manim.py --scenes DecompositionScene ScalabilityScene
"""

from manimlib import *
import argparse
import os
import subprocess
import sys
from pathlib import Path

WAIT_PACING = 3.0
RUN_TIME_PACING = 2.0

# ─── shared style (identical palette to the other two films) ─────────────────

BG_COLOR    = "#0D111E"
ACCENT      = "#64C8FF"
NODE_DEF    = "#263A6C"
NODE_NEW    = "#2DD273"
NODE_CMP    = "#FFC832"
NODE_SWAP   = "#FF5F37"
NODE_DONE   = "#4BAFFF"
NODE_VIS    = "#A05ADC"
NODE_PATH   = "#32DC9C"
TEXT_LIGHT  = "#E6EBFF"
TEXT_DIM    = "#6E7899"
PANEL_BG    = "#161C30"
CODE_BG     = "#0B0F1A"

# semantic colors for this film
C_ELEMENT   = ACCENT          # a data element
C_THREAD    = NODE_NEW        # a thread
C_CTA       = NODE_CMP        # a CTA / block
C_GRID      = NODE_VIS        # a grid
C_CORE      = NODE_DONE       # a processing core
C_SHARED    = NODE_PATH       # shared memory / cooperation
C_VS        = "#5A7CFF"       # vertex-shader state
C_GS        = "#FFA23C"       # geometry-shader state
C_PS        = "#A05ADC"       # pixel-shader state

CHAPTER_TITLE_SIZE = 60
SECTION_TITLE_SIZE = 42
BODY_SIZE          = 28
CAPTION_SIZE       = 20


# ─── tiny helpers (same signatures as the other two scripts) ─────────────────

def panel(width, height, color=PANEL_BG, stroke=NODE_DEF, stroke_w=2):
    return Rectangle(width=width, height=height,
                     fill_color=color, fill_opacity=1.0,
                     stroke_color=stroke, stroke_width=stroke_w)


def labeled_box(text, width=2.6, height=0.9, fill=NODE_DEF, stroke=ACCENT,
                text_color=TEXT_LIGHT, text_scale=0.5):
    rect = Rectangle(width=width, height=height,
                     fill_color=fill, fill_opacity=0.85,
                     stroke_color=stroke, stroke_width=2)
    label = Text(text, color=text_color).scale(text_scale)
    label.move_to(rect.get_center())
    return VGroup(rect, label)


def caption(text, scale=0.45, color=TEXT_DIM):
    return Text(text, color=color).scale(scale)


def section_title(text):
    return Text(text, color=TEXT_LIGHT).scale(SECTION_TITLE_SIZE / 48)


def footer(text):
    return caption(text, scale=0.40, color=TEXT_DIM)


def cell_grid(rows, cols, size=0.34, buff=0.06, fill=C_ELEMENT,
              stroke=NODE_DEF, opacity=0.9):
    """A rows x cols block of small squares — the universal building block
    of this film (data elements, threads, CTAs, cores...)."""
    g = VGroup()
    for r in range(rows):
        for c in range(cols):
            sq = Square(side_length=size, fill_color=fill,
                        fill_opacity=opacity, stroke_color=stroke,
                        stroke_width=1.2)
            sq.move_to(RIGHT * c * (size + buff) + DOWN * r * (size + buff))
            g.add(sq)
    g.center()
    g.rows, g.cols = rows, cols
    return g


def tile_box(label, color, width=1.5, height=1.5, text_scale=0.34):
    """A labeled tile used for block / CTA / grid representations."""
    rect = Rectangle(width=width, height=height,
                     fill_color=PANEL_BG, fill_opacity=1.0,
                     stroke_color=color, stroke_width=2.5)
    txt = Text(label, color=color).scale(text_scale)
    txt.move_to(rect.get_center())
    grp = VGroup(rect, txt)
    grp.rect, grp.txt = rect, txt
    return grp


# ─── Chapter 1 — title card ──────────────────────────────────────────────────

class FilmIntro(Scene):
    def construct(self):
        self.camera.background_color = BG_COLOR

        title = Text("How a GPU Carves Up a Problem", color=TEXT_LIGHT)
        title.scale(CHAPTER_TITLE_SIZE / 48)
        subtitle = Text("Threads, CTAs, grids — and write-once, scale-anywhere",
                        color=ACCENT).scale(0.56)
        subtitle.next_to(title, DOWN, buff=0.35)
        attribution = caption(
            "Concept: scalable parallelism decomposition",
            scale=0.42)
        attribution.next_to(subtitle, DOWN, buff=0.9)

        self.play(Write(title), run_time =  RUN_TIME_PACING * 1.6)
        self.play(FadeIn(subtitle, shift=UP * 0.3), run_time =  RUN_TIME_PACING * 1.0)
        self.play(FadeIn(attribution), run_time =  RUN_TIME_PACING * 0.8)
        self.wait( WAIT_PACING * 1.2)
        self.play(FadeOut(VGroup(title, subtitle, attribution)), run_time =  RUN_TIME_PACING * 1.8)


# ─── Chapter 2 — the problem: explicit parallelism doesn't scale ─────────────

class ProblemScene(Scene):
    """Old model: code names specific cores. Move it to a different GPU and
    it breaks, under-uses, or won't run. Motivates a scalable abstraction."""

    def construct(self):
        self.camera.background_color = BG_COLOR

        heading = section_title("The Problem: Code Tied to Hardware")
        heading.to_edge(UP, buff=0.6)
        self.play(Write(heading), run_time =  RUN_TIME_PACING * 1.0)

        sub = caption("Old way: the program explicitly names which cores to use.",
                      scale=0.48, color=TEXT_LIGHT)
        sub.next_to(heading, DOWN, buff=0.35)
        self.play(FadeIn(sub), run_time =  RUN_TIME_PACING * 0.8)

        # a little "program" written for a 2-core machine
        prog = panel(4.6, 2.0, color=CODE_BG, stroke=NODE_DEF)
        prog.move_to(LEFT * 3.4 + UP * 0.1)
        prog_lines = VGroup(*[
            caption(t, scale=0.40, color=TEXT_LIGHT) for t in [
                "run task A on core 0",
                "run task B on core 1",
                "# written for a 2-core GPU",
            ]
        ]).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        prog_lines.move_to(prog.get_center())
        prog_lbl = caption("program", scale=0.40, color=ACCENT)
        prog_lbl.next_to(prog, UP, buff=0.18)
        self.play(FadeIn(prog), FadeIn(prog_lbl),
                  LaggedStartMap(FadeIn, prog_lines, lag_ratio=0.2),
                  run_time =  RUN_TIME_PACING * 1.6)

        # the 2-core GPU it was written for — runs fine
        gpu2 = VGroup(*[labeled_box(f"core {i}", width=1.7, height=0.9,
                                    fill=PANEL_BG, stroke=C_CORE,
                                    text_scale=0.36) for i in range(2)])
        gpu2.arrange(DOWN, buff=0.3)
        gpu2.move_to(RIGHT * 3.2 + UP * 0.1)
        gpu2_lbl = caption("2-core GPU — runs fine", scale=0.40, color=NODE_NEW)
        gpu2_lbl.next_to(gpu2, UP, buff=0.2)
        self.play(FadeIn(gpu2), FadeIn(gpu2_lbl), run_time =  RUN_TIME_PACING * 0.9)
        self.play(LaggedStartMap(
            lambda m: Indicate(m, color=NODE_NEW, scale_factor=1.05),
            gpu2, lag_ratio=0.2), run_time =  RUN_TIME_PACING * 1.0)
        self.wait( WAIT_PACING * 0.5)

        # move to a 4-core GPU: 2 cores idle
        gpu4 = VGroup(*[labeled_box(f"core {i}", width=1.7, height=0.78,
                                    fill=PANEL_BG, stroke=C_CORE,
                                    text_scale=0.34) for i in range(4)])
        gpu4.arrange(DOWN, buff=0.22)
        gpu4.move_to(RIGHT * 3.2 + UP * 0.1)
        gpu4_lbl = caption("4-core GPU — 2 cores wasted", scale=0.40,
                           color=NODE_SWAP)
        gpu4_lbl.next_to(gpu4, UP, buff=0.2)
        self.play(FadeOut(gpu2), FadeOut(gpu2_lbl), run_time =  RUN_TIME_PACING * 0.4)
        self.play(FadeIn(gpu4), FadeIn(gpu4_lbl), run_time =  RUN_TIME_PACING * 0.8)
        # cores 0,1 light up; cores 2,3 marked idle
        self.play(Indicate(gpu4[0], color=NODE_NEW, scale_factor=1.05),
                  Indicate(gpu4[1], color=NODE_NEW, scale_factor=1.05),
                  run_time =  RUN_TIME_PACING * 0.7)
        idle = VGroup()
        for i in (2, 3):
            x = Text("idle", color=NODE_SWAP).scale(0.34)
            x.move_to(gpu4[i].get_center())
            idle.add(x)
            gpu4[i][1].set_opacity(0.25)
        self.play(LaggedStartMap(FadeIn, idle, lag_ratio=0.2), run_time =  RUN_TIME_PACING * 0.7)

        takeaway = caption(
            "Rewrite for every chip? We need a model that scales by itself.",
            scale=0.48, color=TEXT_LIGHT)
        takeaway.to_edge(DOWN, buff=0.6)
        self.play(Write(takeaway), run_time =  RUN_TIME_PACING * 1.3)
        self.wait( WAIT_PACING * 1.5)

        self.play(FadeOut(VGroup(heading, sub, prog, prog_lbl, prog_lines,
                                 gpu4, gpu4_lbl, idle, takeaway)),
                  run_time =  RUN_TIME_PACING * 0.8)


# ─── Chapter 3 — decomposition: problem -> grid / block / element ────────────

class DecompositionScene(Scene):
    """Hierarchically decompose the problem. an HDTV
    image. Whole image = grid; a 16x16 tile = block; one pixel = element."""

    def construct(self):
        self.camera.background_color = BG_COLOR

        heading = section_title("Decompose the Problem")
        heading.to_edge(UP, buff=0.55)
        self.play(Write(heading), run_time =  RUN_TIME_PACING * 1.0)

        sub = caption("Example: render a 1920 x 1080 HDTV image.",
                      scale=0.46, color=TEXT_LIGHT)
        sub.next_to(heading, DOWN, buff=0.3)
        self.play(FadeIn(sub), run_time =  RUN_TIME_PACING * 0.8)

        # level 1: the whole image = a grid
        image = panel(5.0, 2.9, color=CODE_BG, stroke=C_GRID, stroke_w=3)
        image.move_to(ORIGIN + DOWN * 0.2)
        img_lbl = caption("whole image  =  GRID", scale=0.46, color=C_GRID)
        img_lbl.next_to(image, UP, buff=0.22)
        self.play(ShowCreation(image), FadeIn(img_lbl), run_time =  RUN_TIME_PACING * 1.0)
        self.wait( WAIT_PACING * 0.5)

        # level 2: divide into blocks (tiles)
        blocks = VGroup()
        brows, bcols = 3, 5
        bw = image.get_width() / bcols
        bh = image.get_height() / brows
        for r in range(brows):
            for c in range(bcols):
                b = Rectangle(width=bw * 0.92, height=bh * 0.92,
                              fill_color=PANEL_BG, fill_opacity=0.9,
                              stroke_color=C_CTA, stroke_width=1.8)
                b.move_to(image.get_corner(UL)
                          + RIGHT * (bw * (c + 0.5))
                          + DOWN * (bh * (r + 0.5)))
                blocks.add(b)
        blk_lbl = caption("divide into BLOCKS  (16 x 16-pixel tiles)",
                          scale=0.44, color=C_CTA)
        blk_lbl.next_to(image, DOWN, buff=0.3)
        self.play(LaggedStartMap(FadeIn, blocks, lag_ratio=0.05),
                  FadeIn(blk_lbl), run_time =  RUN_TIME_PACING * 1.8)
        self.wait( WAIT_PACING * 0.4)

        # level 3: zoom one block to its elements (pixels)
        focus = blocks[7]   # a middle block
        self.play(focus.animate.set_stroke(ACCENT, width=3.5),
                  run_time =  RUN_TIME_PACING * 0.5)
        elems = cell_grid(6, 6, size=0.13, buff=0.03, fill=C_ELEMENT,
                          stroke=NODE_DEF)
        elems.move_to(focus.get_center())
        # blow it up to a callout on the right would crowd; instead pulse in place
        callout = cell_grid(8, 8, size=0.16, buff=0.03, fill=C_ELEMENT,
                            stroke=NODE_DEF)
        callout.move_to(RIGHT * 4.6 + DOWN * 0.2)
        callout_lbl = caption("each block = ELEMENTS\n(one pixel each)",
                              scale=0.36, color=C_ELEMENT)
        callout_lbl.next_to(callout, UP, buff=0.2)
        link = DashedLine(focus.get_corner(UR), callout.get_corner(UL),
                          color=TEXT_DIM, stroke_width=1.5)
        self.play(ShowCreation(link),
                  FadeIn(callout_lbl),
                  LaggedStartMap(FadeIn, callout, lag_ratio=0.02),
                  run_time =  RUN_TIME_PACING * 1.6)

        takeaway = caption(
            "Three levels: GRID -> BLOCKS -> ELEMENTS. Any data-parallel "
            "problem fits this shape.",
            scale=0.44, color=TEXT_LIGHT)
        takeaway.to_edge(DOWN, buff=0.5)
        self.play(Write(takeaway), run_time =  RUN_TIME_PACING * 1.4)
        self.wait( WAIT_PACING * 1.6)

        self.play(FadeOut(VGroup(heading, sub, image, img_lbl, blocks,
                                 blk_lbl, callout, callout_lbl, link,
                                 takeaway)), run_time =  RUN_TIME_PACING * 0.8)


# ─── Chapter 4 — the hierarchy maps to threads / CTAs / grids ────────────────

class HierarchyScene(Scene):
    """The problem decomposition maps 1:1 onto the programming model:
    element -> thread, block -> CTA, grid -> grid of CTAs."""

    def construct(self):
        self.camera.background_color = BG_COLOR

        heading = section_title("Map It to the Programming Model")
        heading.to_edge(UP, buff=0.6)
        self.play(Write(heading), run_time =  RUN_TIME_PACING * 1.0)

        # three correspondence rows: problem term  ->  model term
        rows_data = [
            ("ELEMENT", C_ELEMENT, "THREAD", C_THREAD,
             "one instance of the program, one unique thread ID"),
            ("BLOCK",   C_CTA,     "CTA",    C_CTA,
             "a cooperative thread array — threads that work together"),
            ("GRID",    C_GRID,    "GRID",   C_GRID,
             "many independent CTAs — the whole problem"),
        ]
        rows = VGroup()
        for prob, pc, mod, mc, desc in rows_data:
            left = labeled_box(prob, width=2.2, height=0.85, fill=PANEL_BG,
                               stroke=pc, text_scale=0.40)
            arrow = Arrow(LEFT * 0.5, RIGHT * 0.5, buff=0,
                          color=TEXT_DIM, stroke_width=3)
            right = labeled_box(mod, width=2.0, height=0.85, fill=PANEL_BG,
                                stroke=mc, text_scale=0.40)
            desc_t = caption(desc, scale=0.38, color=TEXT_LIGHT)
            row = VGroup(left, arrow, right, desc_t).arrange(RIGHT, buff=0.4)
            rows.add(row)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.7)
        rows.move_to(ORIGIN + DOWN * 0.1)

        for row in rows:
            self.play(FadeIn(row[0]), run_time =  RUN_TIME_PACING * 0.4)
            self.play(GrowArrow(row[1]),
                      FadeIn(row[2], shift=RIGHT * 0.2), run_time =  RUN_TIME_PACING * 0.45)
            self.play(FadeIn(row[3]), run_time =  RUN_TIME_PACING * 0.5)

        note = caption(
            "Each thread uses its thread ID + CTA ID to find exactly which "
            "data to process.",
            scale=0.44, color=ACCENT)
        note.to_edge(DOWN, buff=0.6)
        self.play(Write(note), run_time =  RUN_TIME_PACING * 1.4)
        self.wait( WAIT_PACING * 1.7)

        self.play(FadeOut(VGroup(heading, rows, note)), run_time =  RUN_TIME_PACING * 0.8)


# ─── Chapter 5 — cooperation: CTA threads share + synchronize ────────────────

class CooperationScene(Scene):
    """Threads WITHIN a CTA can share data through fast on-chip memory and
    synchronize at a barrier. Threads in DIFFERENT CTAs cannot. This is the
    distinction that makes fast kernels possible."""

    def construct(self):
        self.camera.background_color = BG_COLOR

        heading = section_title("Why the CTA Matters: Cooperation")
        heading.to_edge(UP, buff=0.55)
        self.play(Write(heading), run_time =  RUN_TIME_PACING * 1.0)

        # one CTA: a row of threads above a shared-memory bar
        threads = VGroup(*[
            Square(side_length=0.62, fill_color=C_THREAD, fill_opacity=0.95,
                   stroke_color=ACCENT, stroke_width=2)
            for _ in range(6)
        ])
        threads.arrange(RIGHT, buff=0.3)
        threads.move_to(UP * 1.3)
        for i, t in enumerate(threads):
            lbl = Text(f"t{i}", color=TEXT_LIGHT).scale(0.30)
            lbl.move_to(t.get_center())
            t.add(lbl)
        t_lbl = caption("threads in ONE CTA", scale=0.42, color=C_THREAD)
        t_lbl.next_to(threads, UP, buff=0.25)

        shared = panel(5.6, 0.7, color=CODE_BG, stroke=C_SHARED, stroke_w=2.5)
        shared.move_to(DOWN * 0.3)
        shared_lbl = caption("fast on-chip SHARED MEMORY", scale=0.40,
                             color=C_SHARED)
        shared_lbl.move_to(shared.get_center())

        self.play(LaggedStartMap(FadeIn, threads, lag_ratio=0.08),
                  FadeIn(t_lbl), run_time =  RUN_TIME_PACING * 1.2)
        self.play(FadeIn(shared), FadeIn(shared_lbl), run_time =  RUN_TIME_PACING * 0.8)

        # step 1: each thread writes into shared memory
        write_arrows = VGroup(*[
            Arrow(t.get_bottom(), shared.get_top() + RIGHT * (t.get_x()
                  - shared.get_x()) * 0.0 + RIGHT * (t.get_x()),
                  buff=0.1, color=C_THREAD, stroke_width=3)
            for t in threads
        ])
        # simpler: vertical arrows straight down
        write_arrows = VGroup()
        for t in threads:
            a = Arrow(t.get_bottom(),
                      np.array([t.get_x(), shared.get_top()[1], 0]),
                      buff=0.08, color=C_THREAD, stroke_width=3)
            write_arrows.add(a)
        write_lbl = caption("1. every thread writes its result",
                            scale=0.40, color=TEXT_LIGHT)
        write_lbl.to_edge(DOWN, buff=1.4)
        self.play(LaggedStartMap(GrowArrow, write_arrows, lag_ratio=0.1),
                  FadeIn(write_lbl), run_time =  RUN_TIME_PACING * 1.4)

        # step 2: synchronize — a barrier line
        barrier = DashedLine(shared.get_left() + LEFT * 0.3 + UP * 0.55,
                             shared.get_right() + RIGHT * 0.3 + UP * 0.55,
                             color=NODE_CMP, stroke_width=3)
        barrier_lbl = caption("2. SYNCHRONIZE  (barrier — all wait here)",
                              scale=0.40, color=NODE_CMP)
        barrier_lbl.move_to(write_lbl)
        self.play(FadeOut(write_arrows), run_time =  RUN_TIME_PACING * 0.3)
        self.play(ShowCreation(barrier),
                  Transform(write_lbl, barrier_lbl), run_time =  RUN_TIME_PACING * 1.0)
        self.play(LaggedStartMap(
            lambda m: Indicate(m, color=NODE_CMP, scale_factor=1.08),
            threads, lag_ratio=0.06), run_time =  RUN_TIME_PACING * 1.0)

        # step 3: each thread reads data ANY thread wrote
        read_arrows = VGroup()
        for t in threads:
            a = Arrow(np.array([t.get_x(), shared.get_top()[1], 0]),
                      t.get_bottom(), buff=0.08,
                      color=C_SHARED, stroke_width=3)
            read_arrows.add(a)
        read_lbl = caption("3. now any thread can read any other's result",
                           scale=0.40, color=C_SHARED)
        read_lbl.move_to(write_lbl)
        self.play(FadeOut(barrier), run_time =  RUN_TIME_PACING * 0.3)
        self.play(LaggedStartMap(GrowArrow, read_arrows, lag_ratio=0.1),
                  Transform(write_lbl, read_lbl), run_time =  RUN_TIME_PACING * 1.4)
        self.wait( WAIT_PACING * 0.4)

        note = caption(
            "Threads in DIFFERENT CTAs cannot do this — that independence "
            "is what makes CTAs freely distributable.",
            scale=0.42, color=ACCENT)
        note.to_edge(DOWN, buff=0.5)
        self.play(FadeOut(write_lbl), Write(note), run_time =  RUN_TIME_PACING * 1.4)
        self.wait( WAIT_PACING * 1.6)

        self.play(FadeOut(VGroup(heading, threads, t_lbl, shared, shared_lbl,
                                 read_arrows, note)), run_time =  RUN_TIME_PACING * 0.8)

# ─── Chapter 6 — The Companionship ─────────────
class StateScene(Scene):
    """ Companionship: Each group carries its own state snapshot, so groups with different configs run on shared cores without
    ever draining the machine."""

    def construct(self):
        self.camera.background_color = BG_COLOR

        heading = section_title("Each Group Carries Its Own State")
        heading.to_edge(UP, buff=0.6)
        self.play(Write(heading), run_time =  RUN_TIME_PACING * 1.0)

        sub = caption("Different groups need different setup — without "
                      "stopping the cores.",
                      scale=0.46, color=TEXT_LIGHT)
        sub.next_to(heading, DOWN, buff=0.3)
        self.play(FadeIn(sub), run_time =  RUN_TIME_PACING * 0.8)

        # master register on the left
        master = labeled_box("MASTER\nregister", width=2.3, height=1.3,
                             fill=PANEL_BG, stroke=ACCENT, text_scale=0.36)
        master.to_edge(LEFT, buff=1.0).shift(DOWN * 0.1)
        self.play(FadeIn(master), run_time =  RUN_TIME_PACING * 0.7)

        # three per-group state registers -> three core groups
        groups = [("group 0", C_VS, "vertex-shader state"),
                  ("group 1", C_PS, "pixel-shader state"),
                  ("group 2", C_GS, "geometry-shader state")]
        rows = VGroup()
        for name, color, desc in groups:
            reg = labeled_box(name, width=2.0, height=0.8, fill=CODE_BG,
                              stroke=color, text_scale=0.36)
            desc_t = caption(desc, scale=0.36, color=color)
            row = VGroup(reg, desc_t).arrange(RIGHT, buff=0.4)
            rows.add(row)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.55)
        rows.move_to(RIGHT * 1.6 + DOWN * 0.1)

        # copy state from master into each per-group register, staggered
        for i, row in enumerate(rows):
            arrow = Arrow(master.get_right(), row[0].get_left(),
                          buff=0.15, color=TEXT_DIM, stroke_width=2.5)
            copy_lbl = caption("copy", scale=0.32, color=TEXT_DIM)
            copy_lbl.next_to(arrow, UP, buff=0.05)
            self.play(GrowArrow(arrow), FadeIn(copy_lbl),
                      FadeIn(row, shift=RIGHT * 0.2), run_time =  RUN_TIME_PACING * 0.7)
            self.play(Indicate(row[0], color=row[0][0].get_stroke_color(),
                               scale_factor=1.06),
                      FadeOut(copy_lbl), FadeOut(arrow), run_time =  RUN_TIME_PACING * 0.5)

        note = caption(
            "The master register can be updated for the NEXT group while "
            "current groups keep running — no draining.",
            scale=0.42, color=ACCENT)
        note.to_edge(DOWN, buff=0.55)
        self.play(Write(note), run_time =  RUN_TIME_PACING * 1.4)
        self.wait( WAIT_PACING * 1.7)

        self.play(FadeOut(VGroup(heading, sub, master, rows, note)),
                  run_time =  RUN_TIME_PACING * 0.8)


class ScalabilityScene(Scene):
    """The payoff claim. The SAME grid of independent CTAs runs on 1 core,
    many cores, or many GPUs — the hardware spreads the work."""

    def construct(self):
        self.camera.background_color = BG_COLOR

        heading = section_title("Write Once, Scale Anywhere")
        heading.to_edge(UP, buff=0.55)
        self.play(Write(heading), run_time =  RUN_TIME_PACING * 1.0)

        # the SAME grid of CTAs — a pool of independent tiles
        def make_pool():
            pool = cell_grid(3, 6, size=0.42, buff=0.10, fill=PANEL_BG,
                             stroke=C_CTA, opacity=1.0)
            return pool
        pool = make_pool()
        pool.move_to(UP * 1.7)
        pool_lbl = caption("one grid — 18 independent CTAs (same program)",
                           scale=0.42, color=C_CTA)
        pool_lbl.next_to(pool, UP, buff=0.22)
        self.play(LaggedStartMap(FadeIn, pool, lag_ratio=0.03),
                  FadeIn(pool_lbl), run_time =  RUN_TIME_PACING * 1.4)

        # readout of degree of parallelism
        readout = caption("degree of parallelism: —", scale=0.46,
                          color=ACCENT)
        readout.to_edge(DOWN, buff=1.5)
        self.play(FadeIn(readout), run_time =  RUN_TIME_PACING * 0.5)

        def distribute(core_count, label, par_text):
            """Build a row of `core_count` cores below, animate CTAs flowing
            into them round-robin, update the readout."""
            cores = VGroup(*[
                labeled_box(f"core {i}", width=1.5, height=0.7,
                            fill=PANEL_BG, stroke=C_CORE, text_scale=0.30)
                for i in range(core_count)
            ])
            cores.arrange(RIGHT, buff=0.3)
            cores.move_to(DOWN * 0.6)
            cfg_lbl = caption(label, scale=0.42, color=C_CORE)
            cfg_lbl.next_to(cores, DOWN, buff=0.3)
            self.play(LaggedStartMap(FadeIn, cores, lag_ratio=0.1),
                      FadeIn(cfg_lbl), run_time =  RUN_TIME_PACING * 0.9)

            # round-robin: copy a faded clone of each CTA into a core
            flashes = []
            for idx, cta in enumerate(pool):
                core = cores[idx % core_count]
                flashes.append((cta, core))
            # animate in small batches for pace
            batch = max(1, core_count)
            for start in range(0, len(flashes), batch):
                anims = []
                for cta, core in flashes[start:start + batch]:
                    dot = cta.copy().set_fill(C_CTA, opacity=0.9)
                    dot.set_stroke(C_CTA, width=1.5)
                    anims.append(Succession(
                        dot.animate.move_to(core.get_center()).scale(0.4),
                        Animation(dot, run_time =  RUN_TIME_PACING * 0.01)))
                    self.add(dot)
                self.play(*[a for a in anims], run_time =  RUN_TIME_PACING/2 * 0.45)
                self.play(*[Indicate(c, color=C_CORE, scale_factor=1.06)
                            for c in cores], run_time =  RUN_TIME_PACING * 0.3)
                # clean up the dots
                self.remove(*[m for m in self.mobjects
                              if isinstance(m, Square)
                              and m not in pool and m not in [
                                  x for cc in cores for x in cc]])

            new_readout = caption(f"degree of parallelism: {par_text}",
                                  scale=0.46, color=ACCENT).move_to(readout)
            self.play(Transform(readout, new_readout), run_time =  RUN_TIME_PACING * 0.5)
            self.wait( WAIT_PACING * 0.8)
            return VGroup(cores, cfg_lbl)

        # 6A: one core — CTAs run sequentially
        stage = distribute(1, "minimal: 1 GPU x 1 core — runs sequentially",
                           "16")
        self.wait( WAIT_PACING * 0.3)
        self.play(FadeOut(stage), run_time =  RUN_TIME_PACING * 0.5)

        # 6B: four cores — CTAs spread across cores
        stage = distribute(4, "medium: 1 GPU x 4 cores — 4x faster", "64")
        self.wait( WAIT_PACING * 0.3)
        self.play(FadeOut(stage), run_time =  RUN_TIME_PACING * 0.5)

        # 6C: many cores (stand-in for many GPUs x many cores)
        stage = distribute(6, "large: many GPUs x many cores", "2048")
        self.wait( WAIT_PACING * 0.3)

        takeaway = caption(
            "Identical code, identical result — only the TIME changes. "
            "The hardware does the spreading.",
            scale=0.44, color=TEXT_LIGHT)
        takeaway.to_edge(DOWN, buff=0.55)
        self.play(FadeOut(readout), Write(takeaway), run_time =  RUN_TIME_PACING * 1.4)
        self.wait( WAIT_PACING * 1.6)

        self.play(FadeOut(VGroup(heading, pool, pool_lbl, stage, takeaway)),
                  run_time =  RUN_TIME_PACING * 0.8)


# ─── Chapter 8 — payoff: the model under modern AI ───────────────────────────

class PayoffScene(Scene):
    """The filter example, with the data swapped: a tiled matrix
    multiply is decomposed exactly the same way — and that is the operation
    under every transformer layer."""

    def construct(self):
        self.camera.background_color = BG_COLOR

        heading = section_title("The Same Model, Under Modern AI")
        heading.to_edge(UP, buff=0.6)
        self.play(Write(heading), run_time =  RUN_TIME_PACING * 1.0)

        sub = caption("Swap 'pixel tile' for 'matrix tile' — the operation "
                      "under every transformer layer.",
                      scale=0.44, color=TEXT_LIGHT)
        sub.next_to(heading, DOWN, buff=0.3)
        self.play(FadeIn(sub), run_time =  RUN_TIME_PACING * 0.8)

        # output matrix = grid; each tile = CTA; each element = thread
        out = panel(3.4, 3.4, color=CODE_BG, stroke=C_GRID, stroke_w=3)
        out.move_to(LEFT * 3.2 + DOWN * 0.3)
        out_lbl = caption("output matrix = GRID", scale=0.40, color=C_GRID)
        out_lbl.next_to(out, UP, buff=0.18)
        tiles = VGroup()
        for r in range(4):
            for c in range(4):
                t = Square(side_length=out.get_width() / 4 * 0.9,
                           fill_color=PANEL_BG, fill_opacity=0.9,
                           stroke_color=C_CTA, stroke_width=1.6)
                t.move_to(out.get_corner(UL)
                          + RIGHT * (out.get_width() / 4 * (c + 0.5))
                          + DOWN * (out.get_height() / 4 * (r + 0.5)))
                tiles.add(t)
        self.play(ShowCreation(out), FadeIn(out_lbl), run_time =  RUN_TIME_PACING * 0.9)
        self.play(LaggedStartMap(FadeIn, tiles, lag_ratio=0.04),
                  run_time =  RUN_TIME_PACING * 1.4)

        tile_note = caption("each tile = a CTA\neach element = a thread",
                            scale=0.38, color=C_CTA)
        tile_note.next_to(out, DOWN, buff=0.3)
        self.play(FadeIn(tile_note),
                  Indicate(tiles[5], color=ACCENT, scale_factor=1.1),
                  run_time =  RUN_TIME_PACING * 1.0)

        # dependent grids = layers of a network
        layers = VGroup(*[
            labeled_box(t, width=2.0, height=0.9, fill=PANEL_BG,
                        stroke=C_GRID, text_scale=0.34)
            for t in ["Layer N\n(grid)", "Layer N+1\n(grid)",
                      "Layer N+2\n(grid)"]
        ])
        layers.arrange(DOWN, buff=0.5)
        layers.move_to(RIGHT * 3.4 + DOWN * 0.3)
        arrows = VGroup(*[
            Arrow(layers[i].get_bottom(), layers[i + 1].get_top(),
                  buff=0.08, color=TEXT_DIM, stroke_width=3)
            for i in range(len(layers) - 1)
        ])
        layers_lbl = caption("dependent grids = network layers", scale=0.38,
                             color=C_GRID)
        layers_lbl.next_to(layers, UP, buff=0.2)
        self.play(FadeIn(layers[0]), FadeIn(layers_lbl), run_time =  RUN_TIME_PACING * 0.6)
        for i in range(len(layers) - 1):
            self.play(GrowArrow(arrows[i]),
                      FadeIn(layers[i + 1], shift=DOWN * 0.2), run_time =  RUN_TIME_PACING * 0.55)

        takeaway = caption(
            "Decompose, distribute, depend — a 2006 model still describes "
            "how AI runs on GPUs today.",
            scale=0.44, color=TEXT_LIGHT)
        takeaway.to_edge(DOWN, buff=0.85)
        self.play(Write(takeaway), run_time =  RUN_TIME_PACING * 1.4)

        attribution = footer("Source concept: GPU SIMT programming model")
        attribution.to_edge(DOWN, buff=0.45)
        self.play(FadeIn(attribution), run_time =  RUN_TIME_PACING * 0.7)
        self.wait( WAIT_PACING * 1.8)
        self.play(FadeOut(VGroup(heading, sub, out, out_lbl, tiles, tile_note,
                                 layers, arrows, layers_lbl, takeaway,
                                 attribution)), run_time =  RUN_TIME_PACING * 1.0)


# ─── film order + CLI (same pattern as the other two films) ──────────────────

FILM_ORDER = [
    "FilmIntro",
    "ProblemScene",
    "DecompositionScene",
    "HierarchyScene",
    "CooperationScene",
    "StateScene",
    "ScalabilityScene",
    "PayoffScene",
]

NARRATION = {
    "FilmIntro":
        "Before a GPU can run anything, the problem has to be carved into "
        "pieces. How that carving works is the programming model.",
    "ProblemScene":
        "In the old way, a program named specific cores explicitly. Move "
        "that code to a GPU with more cores and the extra cores sit idle; "
        "move it to one with fewer and it may not run at all. We need a "
        "model that scales by itself.",
    "DecompositionScene":
        "The answer is to decompose the problem hierarchically. Take "
        "an example: rendering an HDTV image. The whole image is "
        "a grid. It divides into blocks — sixteen-by-sixteen pixel tiles. "
        "And each block divides into elements — one pixel each.",
    "HierarchyScene":
        "That decomposition maps directly onto the programming model. Each "
        "element becomes a thread. Each block becomes a cooperative thread "
        "array, or CTA. And the whole grid becomes a grid of CTAs.",
    "CooperationScene":
        "The CTA matters because threads inside one CTA can cooperate. They "
        "write results into fast on-chip shared memory, synchronize at a "
        "barrier, and then read what any other thread produced. Threads in "
        "different CTAs cannot — and that independence is what lets CTAs be "
        "spread freely across hardware.",
    "StateScene":
        "Each group also carries its own state snapshot — its shader "
        "program, its parameters. Because the snapshot is copied per group, "
        "the master configuration can be updated for the next group while "
        "current groups keep running. The machine never has to drain.",
    "ScalabilityScene":
        "Here is the payoff. The same grid of independent CTAs runs on one "
        "core, on many cores, or across many GPUs. The hardware spreads the "
        "work. The code is identical, the result is identical — only the "
        "time taken changes.",
    "PayoffScene":
        "Swap the pixel tile for a matrix tile and the same model "
        "describes a tiled matrix multiply — the operation under every "
        "transformer layer. Dependent grids become network layers. A 2006 "
        "programming model still describes how AI runs on GPUs today.",
}


def render_scene(name, resolution, outdir):
    cmd = ["manimgl", __file__, name, "-w",
           "--resolution", resolution,
           "--video_dir", str(outdir)]
    print("  $", " ".join(cmd))
    subprocess.run(cmd, check=True)


def make_narration(name, outdir):
    text = NARRATION.get(name, "")
    if not text:
        return None
    wav = outdir / f"{name}.wav"
    subprocess.run(["espeak-ng", "-s", "150", "-w", str(wav), text],
                   check=True)
    return wav


def stitch(outdir, resolution, narrate):
    clips = []
    for name in FILM_ORDER:
        mp4 = outdir / f"{name}.mp4"
        if not mp4.exists():
            print(f"  ! missing {mp4}, skipping")
            continue
        if narrate:
            wav = outdir / f"{name}.wav"
            if wav.exists():
                muxed = outdir / f"{name}_av.mp4"
                subprocess.run(
                    ["ffmpeg", "-y", "-i", str(mp4), "-i", str(wav),
                     "-c:v", "copy", "-c:a", "aac", "-shortest",
                     str(muxed)], check=True)
                clips.append(muxed)
                continue
        clips.append(mp4)

    listfile = outdir / "concat.txt"
    listfile.write_text("".join(f"file '{c}'\n" for c in clips))
    final = outdir / "simt_programming_model_film.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
         "-c", "copy", str(final)], check=True)
    print(f"\n  Film written: {final}")


def main():
    ap = argparse.ArgumentParser(
        description="Render the SIMT programming-model explainer film.")
    ap.add_argument("--all", action="store_true",
                    help="render every scene and stitch the film")
    ap.add_argument("--scenes", nargs="+",
                    help="render only these scene class names")
    ap.add_argument("--resolution", default="3840x2160",
                    help="WIDTHxHEIGHT, default 3840x2160 (4K)")
    ap.add_argument("--narrate", action="store_true",
                    help="generate espeak-ng narration and mux it in")
    ap.add_argument("--outdir", default="simt_model_out",
                    help="output directory")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if args.scenes:
        names = args.scenes
    elif args.all:
        names = FILM_ORDER
    else:
        ap.print_help()
        sys.exit(0)

    for name in names:
        print(f"\n=== {name} ===")
        render_scene(name, args.resolution, outdir)
        if args.narrate:
            make_narration(name, outdir)

    if args.all:
        print("\n=== stitching film ===")
        stitch(outdir, args.resolution, args.narrate)


if __name__ == "__main__":
    main()
