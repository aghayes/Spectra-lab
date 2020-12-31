import sys
import spectra

if len(sys.argv) > 1:
    sys.argv = [sys.argv[x].replace("'", "").replace('"', "") for x in range(len(sys.argv))]
    path_to = sys.argv[1]
    if ".csv" not in path_to:
        concat_csv = sys.argv[2]
        path_out = sys.argv[3]
        if len(sys.argv) > 4:
            chart_save_path = sys.argv[4]
        else:
            chart_save_path = None
        processor = spectra.Main(path_to, concat_csv)
    else:
        path_out = sys.argv[2]
        if len(sys.argv) > 3:
            chart_save_path = sys.argv[3]
        else:
            chart_save_path = None
        processor = spectra.Main(path_to)
else:
    path_to = input("Path to concatenated CSV or spectra directory: ")
    if ".csv" not in path_to:
        concat_csv = input("Path to save concatenated CSV: ")
        processor = spectra.Main(path_to, concat_csv)
    else:
        processor = spectra.Main(path_to)

    path_out = input("Path to save analyzed data CSV: ")
    chart_save_path = input("Path to save charts to: ")

csv_save_path = "./{}".format(path_out) if not any(x in path_out for x in ['/', '\\']) else path_out
if ".csv" not in csv_save_path:
    csv_save_path = csv_save_path + ".csv"


processor.analyze_to_file(csv_save_path, chart_save_path)

