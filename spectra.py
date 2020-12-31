import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import constants as C


class Main:
    def __init__(self, dir_path=None, csv_save_path=None):
        if dir_path:
            self.dir_path = "./{}".format(dir_path) if not any(x in dir_path
                                                               for x in ['/', '\\']) else dir_path
        else:
            path_in = input("Path to spectra: ")
            self.dir_path = "./{}".format(path_in) if not any(x in path_in
                                                              for x in ['/', '\\']) else path_in
        if ".csv" in self.dir_path:
            self.spectra = pd.read_csv(self.dir_path, index_col=0)
        else:
            if csv_save_path:
                self.csv_save_path = "./{}".format(csv_save_path) if not any(x in dir_path
                                                                             for x in ['/', '\\']) else csv_save_path
                if ".csv" not in self.csv_save_path:
                    self.csv_save_path = self.csv_save_path + ".csv"
            else:
                path_out = input("Path to save concatenated csv: ")
                self.csv_save_path = "./{}".format(path_out) if not any(x in path_out
                                                                        for x in ['/', '\\']) else path_out
                if ".csv" not in self.csv_save_path:
                    self.csv_save_path = self.csv_save_path + ".csv"

            def file_sort(path):
                hms = [float(x) for x in re.findall(r"(\d*\.\d*)(?:[hms])", path)]
                hms = hms[0] + hms[1]/60 + hms[2]/3600
                return hms

            self.file_list = [self.dir_path + "/" + file for file in sorted(os.listdir(self.dir_path), key=file_sort)]

            self.spectra = self.concatenate_spectra()

    def concatenate_spectra(self):
        spectra = pd.read_csv(self.file_list[0], names=['frequencies'], usecols=[0], index_col=0)
        for file in self.file_list:
            coordinates = re.findall('(?:spectra-)(.*)(?:.csv)', file)[0].replace('x', 'X')
            file_frame = pd.read_csv(file,
                                     names=['frequencies', coordinates],
                                     index_col=0,
                                     usecols=[0, 3])
            spectra = pd.concat([spectra, file_frame], axis=1,)
        spectra.to_csv(self.csv_save_path)
        return spectra

    # takes a DataFrame with a list of frequency peaks and calculates the speed of the emitting object
    def calc_speed(self, pf: pd.DataFrame):
        df = pf.copy(deep=True)
        df = df['frequency']

        df = df.apply(self.calc_redshift)
        df = df.apply(self.calc_relativistic_doppler)

        velocity_and_power = pd.concat([df, pf['power']], axis=1)
        velocity_and_power = velocity_and_power.rename(columns={"frequency": "velocity"})
        velocity_and_power = pd.concat([pf['frequency'], velocity_and_power], axis=1)

        return velocity_and_power

    def analyze_to_file(self, csv_path, chart_save_path):
        peak_frame = self.detect_peaks(self.spectra, chart_save_path)
        velocity = self.calc_speed(peak_frame)
        velocity.to_csv(csv_path)

    @staticmethod
    def detect_peaks(sf: pd.DataFrame, plot_save_path=None):
        plot_save_path = "./{}/".format(plot_save_path) if not any(x in plot_save_path
                                                                   for x in ["\\", "/"]) else plot_save_path
        plot_save_path = "{}/".format(plot_save_path) if not any(x in plot_save_path[-1]
                                                                 for x in ["\\", "/"]) else plot_save_path
        if not os.path.exists(plot_save_path):
            os.makedirs(plot_save_path)

        def weighting(x, y=0):
            if x[x.index[0]] > y:
                for i in x.index:
                    if not x[i] < y:
                        x[i] = y
                    else:
                        break
                for i in reversed(x.index):
                    if not x[i] < y:
                        x[i] = y
                    else:
                        break

            elif x[x.index[0]] < y:
                for i in x.index:
                    if not x[i] > y:
                        x[i] = y
                    else:
                        break
                for i in reversed(x.index):
                    if not x[i] > y:
                        x[i] = y
                    else:
                        break
            return x

        df = sf.copy(deep=True)
        df = df.rolling(9, min_periods=1, center=True).mean()

        df = df.apply(weighting, axis=0)
        low = df.rolling(1000, center=True).median()
        df = df.apply(lambda x: weighting(x, low.min()[x.name]))
        averages = df.rolling(50, center=True).mean()

        if plot_save_path:
            fig, ax = plt.subplots()
            for column in df.columns:
                ax.clear()
                ax.set_xlim([df.index[0], df.index[-1]])
                ax.set_ylim([averages.min().min()-5, averages.max().max()+5])
                ax.plot(df.index.to_list(), sf[column].to_list(),
                        label="frequency", color="slateblue", alpha=0.5)
                ax.plot(df.index.to_list(), df[column].to_list(),
                        label="frequency mean (n=8)", color="blue")
                ax.set_title(column, fontsize=12)
                ax.axvline(averages[column].idxmax(), ymin=-10, ymax=20, ls='-',
                           label="Peak frequency: " + str(averages[column].idxmax()), color='red')
                ax.axhline(low[column].min(), xmin=0, xmax=1, ls='--',
                           label="Base power: " + str(low[column].min())[:4], color="purple")
                ax.axvline(C.S_LINE, ymin=-10, ymax=20, ls='--', label="H line", color='green')
                ax.legend(loc=3, fontsize=8)
                plt.draw()
                plt.waitforbuttonpress()
                plt.savefig('{}{}.png'.format(plot_save_path, column), bbox_inches='tight')

        peaks = pd.DataFrame({"frequency": averages.idxmax().to_list()}, index=averages.idxmax().index)
        powers = pd.DataFrame({"power": ([sf.at[peaks.at[i, "frequency"], i] -
                                          low.at[low.idxmin()[i], i] for i in peaks.index])},
                              index=peaks.index)

        return pd.concat([peaks, powers], axis=1)

    # observed and emitted must be in the same units, usually mhz
    @staticmethod
    def calc_redshift(observed: float, emitted=C.S_LINE):
        z = (float(observed)/emitted) - 1
        return z

    # z is redshift from calc_redshift, C.C is the speed of light from constants.py currently in m/s
    @staticmethod
    def calc_relativistic_doppler(z):
        v = (C.C*(z**2) + 2*C.C*z)/((z**2) + 2*z + 2)
        return v
