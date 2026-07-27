
#!/usr/bin/env python3
"""
merge_entity_extractions.py

Merge two Graph-RAG entity extraction outputs into a single entity/mention dataset.

Inputs (default):
  outputs/03_entity_extraction/
      ahd_entities_llm.csv
      ahd_entity_mentions_llm.csv
      entities_master.csv
      entity_mentions.csv

Outputs:
  ahd_entities_llm_merged.csv
  ahd_entity_mentions_llm_merged.csv
"""
from pathlib import Path
import argparse
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent if SCRIPT_DIR.name == "scripts" else SCRIPT_DIR

DEFAULT_ENTITY_DIR = BASE_DIR / "outputs" / "03_entity_extraction"


def normalize_ar(s):
    if pd.isna(s):
        return ""
    s=str(s).strip().lower()
    repl={"أ":"ا","إ":"ا","آ":"ا","ى":"ي","ة":"ه","ؤ":"و","ئ":"ي"}
    for a,b in repl.items():
        s=s.replace(a,b)
    return " ".join(s.split())

def parse_aliases(v):
    if pd.isna(v): return []
    t=str(v).strip()
    if not t: return []
    for sep in ["|",";"]:
        t=t.replace(sep,",")
    return [x.strip() for x in t.split(",") if x.strip()]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--my", default=str(DEFAULT_ENTITY_DIR))
    ap.add_argument("--teammate", default=str(DEFAULT_ENTITY_DIR))
    ap.add_argument("--output", default=str(DEFAULT_ENTITY_DIR))
    args=ap.parse_args()

    my = Path(args.my).resolve()
    tm = Path(args.teammate).resolve()
    out = Path(args.output).resolve()
    out.mkdir(parents=True,exist_ok=True)


    print("My folder       :", my)
    print("Teammate folder :", tm)
    print("Output folder   :", out)
    print()

    print((my / "ahd_entities_llm.csv").exists())
    print((my / "ahd_entity_mentions_llm.csv").exists())
    print((tm / "entities_master.csv").exists())
    print((tm / "entity_mentions.csv").exists())

    my_entities=pd.read_csv(my/"ahd_entities_llm.csv")
    my_mentions=pd.read_csv(my/"ahd_entity_mentions_llm.csv")
    tm_entities=pd.read_csv(tm/"entities_master.csv")
    tm_mentions=pd.read_csv(tm/"entity_mentions.csv")

    ent_all=pd.concat([my_entities,tm_entities],ignore_index=True,sort=False)

    merged={}
    old2new={}
    ent_rows=[]
    dup=0

    for _,r in ent_all.iterrows():
        cname=r.get("canonical_name","")
        etype=r.get("entity_type","")
        key=(normalize_ar(cname),etype)
        if key not in merged:
            new_id=f"ent_merge_{len(merged)+1:06d}"
            aliases=set(parse_aliases(r.get("aliases","")))
            aliases.add(str(cname).strip())
            conf=float(r.get("confidence",0) or 0)
            merged[key]={
                "entity_id":new_id,
                "canonical_name":cname,
                "canonical_name_norm":normalize_ar(cname),
                "entity_type":etype,
                "aliases":aliases,
                "confidence":conf,
                "provider":r.get("provider",""),
                "model":r.get("model","")
            }
        else:
            dup+=1
            m=merged[key]
            m["aliases"].update(parse_aliases(r.get("aliases","")))
            m["aliases"].add(str(cname).strip())
            try:
                c=float(r.get("confidence",0) or 0)
                if c>m["confidence"]:
                    m["confidence"]=c
            except: pass
        if "entity_id" in r and pd.notna(r["entity_id"]):
            old2new[str(r["entity_id"])]=merged[key]["entity_id"]

    for m in merged.values():
        ent_rows.append({
            "entity_id":m["entity_id"],
            "canonical_name":m["canonical_name"],
            "canonical_name_norm":m["canonical_name_norm"],
            "entity_type":m["entity_type"],
            "aliases":"|".join(sorted(m["aliases"])),
            "confidence":m["confidence"],
            "provider":m["provider"],
            "model":m["model"]
        })
    ent_df=pd.DataFrame(ent_rows)

    men_all=pd.concat([my_mentions,tm_mentions],ignore_index=True,sort=False)
    seen=set()
    out_rows=[]
    unmatched=0
    mdedup=0
    for _,r in men_all.iterrows():
        eid=str(r.get("entity_id",""))
        new=old2new.get(eid)
        if new is None:
            key=(normalize_ar(r.get("canonical_name","")),r.get("entity_type",""))
            rec=merged.get(key)
            if rec:new=rec["entity_id"]
        if new is None:
            unmatched+=1
            continue
        dkey=(new,
              str(r.get("qa_id","")),
              str(r.get("surface_form","")),
              str(r.get("field","")))
        if dkey in seen:
            mdedup+=1
            continue
        seen.add(dkey)
        row=r.to_dict()
        row["entity_id"]=new
        out_rows.append(row)
    men_df=pd.DataFrame(out_rows).reset_index(drop=True)
    if len(men_df):
        men_df["mention_id"]=[f"men_merge_{i+1:07d}" for i in range(len(men_df))]

    ent_path=out/"ahd_entities_llm_merged.csv"
    men_path=out/"ahd_entity_mentions_llm_merged.csv"
    ent_df.to_csv(ent_path,index=False,encoding="utf-8-sig")
    men_df.to_csv(men_path,index=False,encoding="utf-8-sig")

    print("="*45)
    print("MERGE REPORT")
    print("="*45)
    print(f"Your entities:           {len(my_entities)}")
    print(f"Teammate entities:       {len(tm_entities)}")
    print(f"Total before merge:      {len(ent_all)}")
    print(f"Duplicate entities:      {dup}")
    print(f"Final unique entities:   {len(ent_df)}")
    print()
    print(f"Your mentions:           {len(my_mentions)}")
    print(f"Teammate mentions:       {len(tm_mentions)}")
    print(f"Duplicate mentions:      {mdedup}")
    print(f"Final mentions:          {len(men_df)}")
    print(f"Unmatched mentions:      {unmatched}")
    print()
    print("Output:")
    print(f"  {ent_path}")
    print(f"  {men_path}")

if __name__=="__main__":
    main()
