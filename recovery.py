# -*- coding: utf-8 -*-
"""
Created on Mon Dec  7 14:16:51 2020.

@author: etale
"""
import tkinter as tk
import math

rar = [[1000, 200, 125, 30, 12, 4], [600, 120, 100, 3, 4, 1]]
div = [[1, 1, 1, 16, 16, 8], [1, 1, 1, 100, 16, 8]]
qual_d = {0: "Unique", 1: "Rare", 2: "Set", 3: "Magic",
          4: "Superior", 5: "Normal", 6: "Low Quality"}
rk_d = {0: "Normal", 1: "Exceptional"}


class Config:
    """Container for all variables related to the drop."""

    def __init__(self, mlvl, mf, rank, mode):
        """
        Consolidate mlvl, mf, rank and mode into one vector.

        Key:
            mlvl    level of the monster killed
            mf      +% better chance of getting magic items
            rank    is the item normal ( rank=0 ) or exceptional (rank = 1)?
            mode    mf independent (mode = 0) or mf dependent (mode = 1) roll?
        """
        self.mlvl = mlvl
        self.mf = mf
        self.rank = rank
        self.mode = mode

    def single(self, qual):
        """
        Return chance to pass a single roll with this configuration.

        Quality is given by qual, see this table:
            0   unique      4 superior
            1   rare        5 normal
            2   set         6 low quality
            3   magic
        """
        base = rar[self.rank][qual]-int(self.mlvl/div[self.rank][qual])
        if self.mode == 0:
            return 1/max(1, base)
        elif self.mode == 1 and qual <= 3:
            return 1/max(1, int(base*100/self.mf)) if self.mf else 0
        else:
            return 0

    def fail(self):
        """Return chance to fail all rolls of a given mode."""
        return math.prod([1-self.single(q) for q in range(0, 6)])

    def quality(self, qual):
        """
        Return chance to fail all rolls up to qual and pass qual.

        If self.mode = 0 this does not include the magic dependent rolls.
        """
        individual_fails = [1-self.single(q) for q in range(0, qual)]
        return self.single(qual)*math.prod(individual_fails)

    def quality_p(self, qual):
        """Return the total chance for a given quality."""
        mode0 = Config(self.mlvl, self.mf, self.rank, 0)
        mode1 = Config(self.mlvl, self.mf, self.rank, 1)
        if 0 <= qual <= 5:
            if self.mf:
                return mode1.quality(qual)+mode0.quality(qual)*mode1.fail()
            else:
                return mode0.quality(qual)
        elif qual == 6:
            return mode0.fail()*mode1.fail()
        else:
            return 0

    def formated(self):
        """Return a pair of strings of all chances in rank 0 and rank 1."""
        # Store self.rank to reinstate it later.
        temp = self.rank

        # Create the list of quality names with proper spacing.
        l_a = [(qual_d[q]+":").ljust(12) for q in range(0, 7)]

        # First create the string for rank 0.
        self.rank = 0
        l_b = ["{0:.2%}".format(self.quality_p(q)).rjust(13) for q in range(7)]
        str0 = [l_a[q]+l_b[q] for q in range(7)]

        # Secondly create the string for rank 1.
        self.rank = 1
        l_b = ["{0:.2%}".format(self.quality_p(q)).rjust(13) for q in range(7)]
        str1 = [l_a[q]+l_b[q] for q in range(7)]

        # Restore self.rank to its initial value.
        self.rank = temp
        return ("\n".join(str0), "\n".join(str1))


def recovery(mlvl, crash):
    """
    Least mf value s.t. chance for rares is larger or equal that at crash.

    Only interesting for rank = 1 (exceptional) and qual = 0, 1.
    """
    # Chances just before the crash, i.e. at mf = crash.
    state = Config(mlvl, crash, 1, 0)
    fail = state.quality_p(0)
    rare = state.quality_p(1)+state.quality_p(0)

    # Calculate the recovery mf for failed uniques.
    state.mf += 1
    while state.quality_p(0) < fail:
        state.mf += 1
    mf0 = state.mf

    # Calculate the recovery mf for all rares.
    state.mf = crash+1
    while state.quality_p(1)+state.quality_p(0) < rare:
        state.mf += 1
    # Return failed recovery BEFORE rare recovery.
    return mf0, state.mf


def rank_boxes(master, col):
    """Create a labeled box with the chances for rank = col."""
    tk.Label(master, text="{} Items".format(rk_d[col])).grid(row=5, column=col)
    t_box = tk.Text(master, height=7, width=25)
    t_box.grid(row=6, column=col)
    return t_box


def main():
    """Generate the majority of the tkinter widgets."""
    root = tk.Tk()
    root.title("MF Calculator (1.00-1.06)")
    root.geometry("450x320")
    frame1 = tk.Frame(root)
    frame2 = tk.Frame(root)
    frame3 = tk.Frame(root)

    tk.Label(frame1, text="Magic Find").grid(row=0)
    MFe = tk.Entry(frame1)
    MFe.insert(tk.END, "0")

    tk.Label(frame1, text="Monster Level").grid(row=1)
    mlvle = tk.Entry(frame1)
    mlvle.insert(tk.END, "1")

    tk.Label(frame1, text="Local Maximum").grid(row=2)
    crashe = tk.Entry(frame1)
    crashe.insert(tk.END, "150")

    MFe.grid(row=0, column=1)
    mlvle.grid(row=1, column=1)
    crashe.grid(row=2, column=1)

    p_0 = rank_boxes(frame2, 0)
    p_1 = rank_boxes(frame2, 1)

    tk.Label(frame3, text="Recovery from Crash").grid()
    Rec75 = tk.Text(frame3, height=2, width=20)
    Rec75.grid()
    Rec75.insert(tk.END, "-")

    def go_button():
        """Refresh the quality boxes and the recovery box."""
        mf = int(MFe.get())
        mlvl = int(mlvle.get())
        crash = int(crashe.get())
        state = Config(mlvl, mf, 0, 0)

        # Frame 2 manipulations
        p_0.delete("1.0", tk.END)
        p_1.delete("1.0", tk.END)
        p_0.insert(tk.END, state.formated()[0])
        p_1.insert(tk.END, state.formated()[1])

        # Frame 3 manipulations
        Rec75.delete("1.0", tk.END)
        a, b = recovery(mlvl, crash)
        Rec75.insert(tk.END, "All Rares: {}\nFailed Uniques: {}".format(b, a))

    def button_(master):
        """Create "Go!" button to start calculation."""
        tk.Button(master, text="Go!", command=go_button).grid(row=3, column=1)

    button_(frame1)
    frame1.pack()
    frame2.pack()
    frame3.pack()
    root.mainloop()


if __name__ == "__main__":
    main()
