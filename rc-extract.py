## This script will extract the results of the line profiler
## for the CB Azure Client specifically, filters all long functions
## with given cutoffs, outputing a filtered results file containing
## only profiling of functions fitting the cut-offs, and a csv summary
## file containing information about the longest functions and associated
## lines

from re import search
from os import path, walk

time_cutoff = 20 # seconds
perc_cutoff = 75 # % of total functino time spent on this line


results = 'results/'
metaresults = 'metaresults/'
print("Results directory used: {}".format(results))

files = []
for (dirpath, dirnames, filenames) in walk(results):
    for each_file in filenames:
        if ".res" in each_file:
            files.append(path.join(dirpath, each_file))

print("Collected list: {}".format(files))

summary = "{},{},{},{},{}\n".format("Test File", "CB functon", "Total Time (in s)", "Azure Operation", "Time per hit")

filtered = ""

inside = False
capturing = False
purge_line = True

for each_file in files:
    print("Processing: {}\n".format(each_file))
    with open(each_file, 'r') as current:
        for line in current:
            match = search(r'^Total time: ([\.e\-0-9]+) s', line)
            if match:
                inside = False
                capturing = False
                total_time = float(match.group(1))
                if total_time > time_cutoff:
                    inside = True
                    filtered += "Test suite: {}\n".format(each_file)
                    filtered += line
            elif inside:
                match = search(r'^Function: (.+) at line ([0-9]+)', line)
                if match:
                    func_name = match.group(1)
                    line_num = int(match.group(2))
                    capturing = True
                    filtered += line
                elif capturing:
                    if purge_line:
                        complete_contents = ""
                        paran_num = 0
                    filtered += line
                    match = search(r'^\s+([0-9]+)\s+[0-9]+\s+([\.0-9]+)\s+([\.0-9]+)\s+([\.0-9]+)\s+([^\n]+)', line)
                    if match:
                        percentage = float(match.group(4))
                        line_contents = match.group(5)
                        complete_contents += line_contents.replace(" \\", "")
                        paran_num += line_contents.count("(") - line_contents.count(")")
                        purge_line = " \\" not in line_contents and paran_num == 0
                        if percentage > perc_cutoff:
                            line_num = int(match.group(1))
                            line_time = float(match.group(2))/1000000
                            hit_time = float(match.group(3))/1000000
                            summary += "{},\"{}\",{},\"{}\",{}\n".format(each_file.split('/')[-1].replace(".res", ""), func_name, total_time, complete_contents, hit_time)
                    else:
                        match = search(r'^\s+([0-9]+)\s+([^\n]+)', line)
                        if match:
                            line_contents = match.group(2)
                            complete_contents += line_contents.replace(" \\", "")
                            paran_num += line_contents.count("(") - line_contents.count(")")
                            purge_line = " \\" not in line_contents and paran_num == 0
                    



with open(metaresults+"summary.csv", 'w+') as sum_file:
    sum_file.write(summary)

with open(metaresults+"filtered.txt", 'w+') as fil_file:
    fil_file.write(filtered)
