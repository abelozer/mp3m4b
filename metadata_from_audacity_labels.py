with open("audacity_labels.txt", 'r') as audacity:
    with open("FFMETADATA_NEW.txt", 'w') as metafile:
        print(";FFMETADATA1", file=metafile)
        for line in audacity:
            my_variables = line.split('\t')
            chapter_start = str(int(float(my_variables[0]) * 1_000_000_000))
            chapter_end = str(int(float(my_variables[1]) * 1_000_000_000))
            print("", file=metafile)
            print("[CHAPTER]", file=metafile)
            print("START=" + chapter_start, file=metafile)
            print("END=" + chapter_end, file=metafile)
            print("title=" + my_variables[2], file=metafile)
            