
import os
import numpy as np
import matplotlib.pyplot as plt
from random import random
from time import time_ns
from pickle import dump

import ptlib._backend as PTCONFIG
from ptlib.core.metadata import MetadataManager


class Diagram:
    """ Parallel Timing Diagram *** come back """

    # spacing between timing curves in the PTD
    PTD_SPACING = PTCONFIG._DIAGRAM.PTD_SPACING

    # width of strings printed to console
    CONSOLE_WIDTH = PTCONFIG._DIAGRAM.CONSOLE_WIDTH

    # time scaling divider
    TIME_DIV = PTCONFIG._DIAGRAM.TIME_DIV

    def __init__(self,
                 total_jobs: int = None,
                 start_time: int = None,
                 finish_time: int = None,
                 process_names: dict[str] = None,
                 metadata: dict[int, int] = None,
                 *,
                 meta_manager: MetadataManager = None):
        """
        Parameters:
            total_jobs -- int
                The number of jobs processed by the pipeline.
            start_time -- int
                The start time of the main process in nanoseconds.
            finish_time: int
                The finish time of the main process in nanoseconds.
            process_names: dict[task_id, worker_id]
                Dict where each entry is the string name for worker with
                `id=worker_id` assigned to the task with `id=task_id`.
            metadata -- dict[task_id, worker_id][i] = (job_start, job_finish)
                Look at `ptlib.core.metadata.MetadataManager` for a more 
                detailed explanation.
        """

        assert isinstance(
            meta_manager, MetadataManager), f"meta_manager is the wrong type: {type(meta_manager)}"

        self._total_jobs = meta_manager._total_jobs if meta_manager else total_jobs
        self._start = meta_manager._start if meta_manager else start_time
        self._finish = meta_manager._finish if meta_manager else finish_time

        # combine names and metadata
        names = meta_manager._names if meta_manager else process_names
        meta = meta_manager._meta if meta_manager else metadata

        self._meta = {index: (names[index], meta[index])
                      for index in names.keys()}

        # create diagram plots
        self.ax_ptd = plt.subplot2grid((2, 3), (0, 0), colspan=5)
        self.ax_jobs = plt.subplot2grid((2, 3), (1, 0), colspan=1)
        self.ax_times = plt.subplot2grid((2, 3), (1, 1), colspan=1)
        self.ax_rates = plt.subplot2grid((2, 3), (1, 2), colspan=1)

    def show(self):
        """ 
        Displays current graphs by using `plt.show()`. 
        """

        return plt.show()

    def graph_all(self, save_path: str = ""):
        """
        Generates each of the three graphs. If `save_path` is empty, then 
        the graphs are shown. Otherwise, the graphs are written to 
        `save_path` as a .pkl file. 
        """

        self.graph_ptd()
        self.graph_stats()
        self.table_stats()

        if save_path == "":
            self.show()
        else:
            path = os.path.join(save_path + ".pkl")
            print(f"Saving Parallel Timing Diagram to: {path}")
            dump(plt.gcf(), open(path, "wb"))

    def graph_ptd(self):
        """ 
        Generates parallel timing diagram. 
        """

        print("Generating PTD Graph...")

        # set finish time if it is None
        self._finish = self._finish or time_ns()

        # the y value of the top most timing curve
        y = self.PTD_SPACING * len(self._meta)
        for name, metadata in self._meta.values():
            # create PTD curves and decrement y position
            if True:
                self._create_ptd_lines(name, metadata, y)
                y -= self.PTD_SPACING

        # set graph labels
        self.ax_ptd.set_ylabel("High/Low")
        self.ax_ptd.set_xlabel("Unix Time (ns)")
        self.ax_ptd.legend()

    def graph_stats(self):
        """ 
        Displays the PTD statistics as a bar graph. 
        """

        print("Generating PTD Stats Bar Graph...")

        stats = self.get_stats(graph=True)
        names, worker_ids, num_jobs, \
            times_on, times_off, rates_on, rates_off = zip(*stats)

        x = np.arange(len(names))
        width = 0.5

        # jobs
        jobs_bar = self.ax_jobs.bar(x, num_jobs, width)
        self.ax_jobs.bar_label(jobs_bar, padding=2)
        self.ax_jobs.set_ylabel("n")
        self.ax_jobs.set_xticks(x)
        self.ax_jobs.set_xticklabels(names, rotation=315)
        self.ax_jobs.set_title("Number of Jobs")

        # times
        times_on = np.around(np.array(times_on) / self.TIME_DIV, decimals=2)
        times_off = np.around(np.array(times_off) / self.TIME_DIV, decimals=2)
        times_on_bar = self.ax_times.bar(
            x - (width - .15) / 2, times_on, (width - .15), label="On")
        times_off_bar = self.ax_times.bar(
            x + (width - .15) / 2, times_off, (width - .15), label="Off")
        self.ax_times.bar_label(times_on_bar, padding=2)
        self.ax_times.bar_label(times_off_bar, padding=2)
        self.ax_times.set_ylabel("Time (s)")
        self.ax_times.set_xticks(x)
        self.ax_times.set_xticklabels(names, rotation=315)
        self.ax_times.set_title("Time Spent")
        self.ax_times.legend()

        # rates
        rates_on = np.around(np.array(rates_on) * self.TIME_DIV, decimals=2)
        rates_off = np.around(np.array(rates_off) * self.TIME_DIV, decimals=2)
        rates_on_bar = self.ax_rates.bar(
            x - (width - .15) / 2, rates_on, (width - .15), label="On")
        rates_off_bar = self.ax_rates.bar(
            x + (width - .15) / 2, rates_off, (width - .15), label="Off")
        self.ax_rates.bar_label(rates_on_bar, padding=2)
        self.ax_rates.bar_label(rates_off_bar, padding=2)
        self.ax_rates.set_ylabel("Rate (jobs / s)")
        self.ax_rates.set_xticks(x)
        self.ax_rates.set_xticklabels(names, rotation=315)
        self.ax_rates.set_title("Job Rate")
        self.ax_rates.legend()

    def table_stats(self):
        """ 
        Creates a table containing PTD statistics. 
        """

        print("Generating PTD Stats Table...")

    def get_stats(self, graph=False):
        """ 
        Generates and returns PTD statistics. 
        """

        self._finish = self._finish or time_ns()
        stats = list()
        for (task_id, worker_id), (name, metadata) in self._meta.items():

            num_jobs = len(metadata)
            time_on = time_off = 0

            # Start and finish times are specificed by first pair
            assert len(
                metadata) > 0, f"Error: Worker has no metadata stored. | Name: {name}, Metadata: {metadata}"
            off_since, finish = metadata[0]
            metadata = metadata[1:]

            # increment accumulators
            for ont, offt in metadata:
                time_off += ont - off_since
                time_on += offt - ont
                off_since = offt

            # check edge case
            if finish > off_since:
                time_off += finish - off_since

            # calculate rates
            rate_on = num_jobs / time_on if time_on else 0
            rate_off = num_jobs / time_off if time_on else 0

            stats.append((name, worker_id, num_jobs, time_on,
                          time_off, rate_on, rate_off))

        return stats

    def _create_ptd_lines(self, name: str, metadata: list, y: float):
        """ 
        Creates curve on the timing diagram for a single worker.
        """

        # Start and finish times are specificed by first pair
        assert len(
            metadata) > 0, f"Error: PTProcess has no metadata stored. | Name: {name}, Metadata: {metadata}"

        # set inital on/off times
        off_since, finish = metadata[0]
        metadata = metadata[1:]

        # give curve a random color
        color = (random(), random(), random())

        # add label
        self.ax_ptd.hlines(y, off_since, off_since, color=color, label=name)

        # create vertical and horizontal lines
        for ont, offt in metadata:
            self.ax_ptd.hlines(y, off_since, ont, color=color)
            self.ax_ptd.vlines(ont, y, y + 1, color=color)
            self.ax_ptd.hlines(y + 1, ont, offt, color=color)
            self.ax_ptd.vlines(offt, y, y + 1, color=color)
            off_since = offt

        # extend LOW line
        if finish > off_since:
            self.ax_ptd.hlines(y, off_since, finish, color=color)

    def __str__(self):
        """ Formats the timing diagram statistics in a readable way. """

        s = "=" * self.CONSOLE_WIDTH + "\n"

        # print overall performance
        runtime = (self._finish - self._start) / self.TIME_DIV
        jps = self._total_jobs / runtime
        s += "\n*** OVERALL PERFORMANCE: "
        s += f" | Pipeline Runtime: {runtime} s"
        s += f" | Processed {self._total_jobs} jobs @ {jps:.2f} j/s ***\n\n"

        # print job specific performance
        for name, worker_id, num_jobs, time_on, time_off, rate_on, rate_off in self.get_stats():
            stat_array = [time_on / self.TIME_DIV, time_off / self.TIME_DIV,
                          rate_on * self.TIME_DIV, rate_off * self.TIME_DIV]
            time_on, time_off, rate_on, rate_off = np.around(
                stat_array, decimals=2)
            s += f"Task: {name} & Worker ID: {worker_id} -- {num_jobs} jobs"
            s += f" | {time_on} s on, {time_off} s off"
            s += f" | {rate_on} j/s on, {rate_off} j/s off\n"

        s += "\n" + "=" * self.CONSOLE_WIDTH

        return s
