"""PX13 filtered sort: stable subsequence equivalence, no GUI timing claims."""
from functools import cmp_to_key
from pathlib import Path
import random
import unittest

ROOT=Path(__file__).resolve().parents[2]


def compare(a,b,mode):
    # The model deliberately uses ordinary casefold names, not the OS's
    # CompareStringOrdinal collation. This checks stable-filter ordering only.
    if a["folder"]!=b["folder"]:
        return -1 if a["folder"] else 1
    if mode in (4,5):
        x,y=a["type"],b["type"]
        if x!=y:
            return (-1 if x<y else 1)*(1 if mode==4 else -1)
    if mode in (2,6,3,7):
        field="size" if mode in (2,6) else "date"
        x,y=a[field],b[field]
        if (x is None)!=(y is None):
            return 1 if x is None else -1
        if x is not None and x!=y:
            return (-1 if x<y else 1)*(1 if mode in (6,7) else -1)
    if a["name"]!=b["name"]:
        return (-1 if a["name"]<b["name"] else 1)*(-1 if mode==1 else 1)
    return 0


class FilterSortFrontier(unittest.TestCase):
    def test_source_filters_before_stable_sort_without_changing_paging(self):
        src=(ROOT/"app/winui/MainWindow.xaml.cpp").read_text(
            encoding="utf-8-sig")
        fill=src.split("void MainWindow::FillFiles(",1)[1].split(
            "void MainWindow::",1)[0]
        hide=fill.index("if(!state.showHiddenItems){")
        filename=fill.index("if(!state.filenameFilter.empty()){")
        stable=fill.index("std::stable_sort(order.begin(),order.end()")
        group=fill.index("if(state.groupTabCache.pending())")
        self.assertLess(hide,filename)
        self.assertLess(filename,stable)
        self.assertLess(stable,group)
        self.assertIn("order.erase(std::remove_if(",fill)
        self.assertIn("snapshot.logicalIndex(index)",fill)
        self.assertIn("indexedProjection?static_cast<std::uint64_t>(index)",fill)

    def test_filtering_is_stable_subsequence_of_name_type_size_date_sort(self):
        rand=random.Random(29310)
        rows=[]
        for i in range(8000):
            rows.append({
                "id":i,
                "folder":i%17==0,
                "hidden":i%13==0,
                "name":("keep" if i%31==0 else "other")+str(rand.randrange(1300)).zfill(4),
                "type":(".txt",".md",".csv","")[i%4],
                "size":None if i%11==0 else rand.randrange(500),
                "date":None if i%19==0 else rand.randrange(400),
            })
        for mode in range(8):
            with self.subTest(mode=mode):
                survivor=lambda row: not row["hidden"] and row["name"].startswith("keep")
                key=cmp_to_key(lambda a,b:compare(a,b,mode))
                old=[r["id"] for r in sorted(rows,key=key) if survivor(r)]
                new=[r["id"] for r in sorted(filter(survivor,rows),key=key)]
                self.assertEqual(old,new)
                self.assertGreater(len(new),0)
                self.assertLess(len(new),len(rows)//5)


if __name__=="__main__":
    unittest.main()
