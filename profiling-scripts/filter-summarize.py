## This script will extract the results of the line profiler
## for the CB Azure Client specifically, filters all long functions
## with given cutoffs, outputing a filtered results file containing
## only profiling of functions fitting the cut-offs, and a csv summary
## file containing information about the longest functions and associated
## lines

from re import search
from os import path, walk

time_cutoff = 0 # seconds
perc_cutoff = 33 # % of total function time spent on this line


results = '../results/'
metaresults = '../metaresults/'
print("Results directory used: {}".format(results))

files_dict = {}
for (dirpath, dirnames, filenames) in walk(results):
    for each_file in filenames:
        if ".res" in each_file:
            provider = each_file.split('-')[0]
            curr_list = files_dict.get(provider, [])
            curr_list.append(path.join(dirpath, each_file))
            files_dict[provider] = curr_list

print("Collected files:\n{}".format(files_dict))

for key in files_dict.keys():
    provider = key
    files = files_dict[provider]


    summary = "{},{},{},{},{}\n".format("Test File", "CB functon", "Total Time (in s)", "Azure Operation", "Time per hit")

    for each_file in files:
        inside = True
        capturing = True
        purge_line = True
        print("Processing: {}\n".format(each_file))
        with open(metaresults + "filtered-" + each_file.split('/')[-1], 'w+') as \
                fil_file:
            with open(each_file, 'r') as current:
                filtered = ""
                last_time = 1000000000
                all_text = []
                for line in current:
                    match = search(r'^Total time: ([\.e\-0-9]+) s', line)
                    if match:
                        if filtered:
                            all_text.append((last_time, filtered))
                        filtered = ""
                        inside = False
                        capturing = False
                        last_time = float(match.group(1))
                        if last_time > time_cutoff:
                            inside = True
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
                                    summary += "{},\"{}\",{},\"{}\"," \
                                               "{}\n".format(
                                        each_file.split('/')[-1].replace(
                                            ".res", ""), func_name, last_time,
                                        complete_contents, hit_time)
                            else:
                                match = search(r'^\s+([0-9]+)\s+([^\n]+)', line)
                                if match:
                                    line_contents = match.group(2)
                                    complete_contents += line_contents.replace(" \\", "")
                                    paran_num += line_contents.count("(") - line_contents.count(")")
                                    purge_line = " \\" not in line_contents and paran_num == 0
            all_text.sort(key=lambda x: x[0], reverse=True)
            for text in all_text:
                fil_file.write(text[1])

    with open(metaresults+provider+"-summary.csv", 'w+') as sum_file:
        sum_file.write(summary)
