# Inspired by https://youtu.be/N3tRFayqVtk
# https://github.com/davidrmiller/biosim4
import threading
import time
from queue import Queue, Empty
from tkinter import *
from tkinter import messagebox

# from tkinter.ttk import
from board import Board
from display import Display


def simulator(queue: Queue, board_size: tuple[int, int], steps_per_gen: int, population_count: int,
              mutation_factor: float,
              tile_size: int, ):
    board = Board(board_size, steps_per_gen, population_count, mutation_factor)
    screen = Display(board_size, tile_size)
    screen.display(board)

    gen = 0
    Stop = False
    step_wait_ms = 0
    while not Stop:
        print(f"Generation {gen}")
        for step in range(steps_per_gen):
            time.sleep(step_wait_ms / 1000)
            try:
                result = queue.get(False)

                if result == "pause":
                    screen.display(board, True)
                    result = queue.get()
                if not type(result) is str:
                    continue
                elif result == "stop":
                    Stop = True
                    break
                elif result.startswith("SPEED"):
                    step_wait_ms = (100 - int(result[5:])) * 2
            except Empty:
                board.tick()
                screen.display(board)
        if Stop:
            break
        board.tick_round()
        screen.display(board)
        gen += 1
    screen.destroy()


def gui(queue: Queue):
    root = Tk()
    root.wm_title("Tkinter window")

    pop_variable = IntVar()
    pop_variable.set(20)
    tile_size_variable = IntVar()
    tile_size_variable.set(6)
    board_size_variable = StringVar()
    board_size_variable.set("30x30")
    mut_fac_variable = StringVar()
    mut_fac_variable.set("10")
    steps_per_gen_variable = StringVar()
    steps_per_gen_variable.set("15")

    sim_speed_variable = IntVar()
    sim_speed_variable.set(100)

    def start():
        pop = pop_variable.get()
        tile_size = tile_size_variable.get()
        board_size_string = board_size_variable.get()
        mut_fac_string = mut_fac_variable.get()
        steps_per_gen_string = steps_per_gen_variable.get()

        board_size_split = board_size_string.split('x')
        if len(board_size_split) != 2:
            return messagebox.showerror("Please enter the board size like this:\n WidthxHeight (example: 50x50)")
        # TODO: Return sensible errors when someone enters a non int
        board_size = (int(board_size_split[0]), int(board_size_split[1]))
        mut_fac = float(mut_fac_string)
        steps_per_gen = int(steps_per_gen_string)

        tile_count = board_size[0] * board_size[1]
        pop_count = round(tile_count * (pop / 100))
        thread2 = threading.Thread(target=simulator,
                                   args=(queue, board_size, steps_per_gen, pop_count, mut_fac, tile_size))

        thread2.start()

    def stop():
        queue.put("stop")

    def pause():
        queue.put("pause")

    def speed():
        queue.put(f"SPEED{sim_speed_variable.get()}")

    # Title
    title = Label(root, text="Evolution simulator")
    title.grid(row=0, column=0, columnspan=2)

    # Board width and height
    BSizeRow = 1
    LBSize = Label(root, text="Board size")
    EBSize = Entry(root, textvariable=board_size_variable)
    LBSize.grid(row=BSizeRow, column=0, sticky="w")
    EBSize.grid(row=BSizeRow, column=1, sticky="w", columnspan=3)

    # Population slider
    PopRow = 2
    LPop = Label(root, text="Population %")
    SPop = Scale(root, from_=0, to=100, length=200, variable=pop_variable, digits=3, orient="horizontal",
                 showvalue=False)
    LResPop = Label(root, textvariable=pop_variable)
    LPop.grid(row=PopRow, column=0, sticky="w")
    SPop.grid(row=PopRow, column=1, sticky="w", columnspan=3)
    LResPop.grid(row=PopRow, column=5, sticky="w")

    # Steps per generation entry
    StepsRow = PopRow + 1
    LSteps = Label(root, text="Steps per gen")
    ESteps = Entry(root, textvariable=steps_per_gen_variable)
    LSteps.grid(row=StepsRow, column=0, sticky="w")
    ESteps.grid(row=StepsRow, column=1, sticky="w", columnspan=3)

    # Tile size slider
    TileSizeRiw = StepsRow + 1
    LTileSize = Label(root, text="Tile size")
    STileSize = Scale(root, from_=0, to=10, length=200, variable=tile_size_variable, digits=2, orient="horizontal",
                      showvalue=False)
    LTileSizeRes = Label(root, textvariable=tile_size_variable)
    LTileSize.grid(row=TileSizeRiw, column=0, sticky="w")
    STileSize.grid(row=TileSizeRiw, column=1, sticky="w", columnspan=3)
    LTileSizeRes.grid(row=TileSizeRiw, column=5, sticky="w")

    # Mutation Factor
    MutFacRow = TileSizeRiw + 1
    LMutFac = Label(root, text="Mutation Factor")
    EMutFac = Entry(root, textvariable=mut_fac_variable)
    LMutFac.grid(row=MutFacRow, column=0, sticky="w")
    EMutFac.grid(row=MutFacRow, column=1, sticky='w', columnspan=3)

    # Start Stop Pause
    ControlRow = MutFacRow + 1
    LControls = Label(root, text="Controls")
    BStart = Button(root, text="Start", command=start)
    BStop = Button(root, text="Stop", command=stop)
    BPause = Button(root, text="Pause", command=pause)

    LControls.grid(row=ControlRow, column=0, sticky='w')
    BStart.grid(row=ControlRow, column=1)
    BStop.grid(row=ControlRow, column=2)
    BPause.grid(row=ControlRow, column=3)

    # Speed
    SpeedRow = ControlRow + 1
    LSpeed = Label(root, text="Speed")
    SSpeed = Scale(root, from_=0, to=100, length=200, variable=sim_speed_variable, digits=3, orient="horizontal",
                   showvalue=False)
    LSpeedRes = Label(root, textvariable=sim_speed_variable)
    BSpeed = Button(root, text="Set speed", command=speed)

    LSpeed.grid(row=SpeedRow, column=0, sticky="w")
    SSpeed.grid(row=SpeedRow, column=1, sticky="w", columnspan=3)
    LSpeedRes.grid(row=SpeedRow, column=5, sticky="w")
    BSpeed.grid(row=SpeedRow, column=6, sticky="w")

    root.attributes('-type', 'dialog')
    root.mainloop()


if __name__ == '__main__':
    q = Queue()

    thread1 = threading.Thread(target=gui, args=(q,))
    thread1.start()
# TODO: make sure that the action are correct and not turned around or something like that
# TODO: improve performance
# TODO: Add more graphics, things like a gen count
