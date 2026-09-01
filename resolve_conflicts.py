import re, glob

def resolve(path, keep):
    s = open(path, encoding="utf-8").read()
    if "<<<<<<<" not in s:
        return False
    pat = re.compile(r"<<<<<<<[^\n]*\n(.*?)\n?=======\n(.*?)\n?>>>>>>>[^\n]*\n?", re.S)
    def repl(m):
        ours, theirs = m.group(1), m.group(2)
        if ours.strip() == theirs.strip():
            return ours + "\n"
        return (theirs if keep == "theirs" else ours) + "\n"
    open(path, "w", encoding="utf-8").write(pat.sub(repl, s))
    return True

n = 0
for path in glob.glob("**/*.html", recursive=True) + glob.glob("**/*.xml", recursive=True):
    keep = "ours" if "beijing-interview-preview" in path else "theirs"
    if resolve(path, keep):
        print("resolved:", path); n += 1
print("TOTAL RESOLVED:", n)
