import os
import zipfile
import re
import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from features.extractor import extract_extended_features, FEATURE_NAMES

ZIP_PATH = "torgo_data/archive (3).zip"
STAMMER_DIR = "torgo_data/stammer"
CATEGORIES = ["Block", "Interjection", "Prolongation", "SoundRep", "WordRep"]
SAMPLES_PER_CAT = 200  # 200 * 5 = 1000 balanced stammer samples

def get_speaker_from_filename(filename: str) -> str:
    base = os.path.basename(filename)
    m = re.match(r"^([A-Za-z]+_\d+)", base) or re.match(r"^([A-Za-z]+)", base)
    if m:
        return m.group(1)
    return "stammer_speaker"

def extract_and_select_files():
    print(f"Opening {ZIP_PATH}...")
    if not os.path.exists(ZIP_PATH):
        raise FileNotFoundError(f"{ZIP_PATH} not found.")

    os.makedirs(STAMMER_DIR, exist_ok=True)
    selected_files = []

    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        all_namelist = z.namelist()
        for cat in CATEGORIES:
            cat_dir = os.path.join(STAMMER_DIR, cat)
            os.makedirs(cat_dir, exist_ok=True)
            
            # Find all wavs in this category
            cat_wavs = [n for n in all_namelist if f"/{cat}/" in n and n.endswith(".wav")]
            print(f"Found {len(cat_wavs)} files in category '{cat}'")
            
            # Distribute selection across different speaker prefixes
            by_speaker = {}
            for w in cat_wavs:
                spk = get_speaker_from_filename(w)
                by_speaker.setdefault(spk, []).append(w)
                
            chosen = []
            spk_list = list(by_speaker.keys())
            idx = 0
            while len(chosen) < SAMPLES_PER_CAT and spk_list:
                spk = spk_list[idx % len(spk_list)]
                if by_speaker[spk]:
                    chosen.append(by_speaker[spk].pop(0))
                else:
                    spk_list.remove(spk)
                idx += 1
                
            print(f"Selected {len(chosen)} diverse audio clips for category '{cat}'")
            
            for src_name in chosen:
                filename = os.path.basename(src_name)
                dest_path = os.path.join(cat_dir, filename)
                if not os.path.exists(dest_path):
                    with open(dest_path, "wb") as f_out:
                        f_out.write(z.read(src_name))
                selected_files.append((dest_path, cat))
                
    return selected_files

def process_single_audio(item):
    filepath, category = item
    try:
        feats = extract_extended_features(filepath)
        if feats is None:
            return None
        speaker_id = get_speaker_from_filename(filepath)
        feats["speaker_id"] = speaker_id
        feats["gender"] = "female" if "women" in speaker_id.lower() else ("male" if "he" in speaker_id.lower() else "unspecified")
        feats["disorder_type"] = "stammer"
        feats["severity"] = category.lower()
        feats["audio_path"] = filepath.replace("\\", "/")
        return feats
    except Exception as e:
        return None

def main():
    selected_items = extract_and_select_files()
    print(f"\nTotal stammer files extracted: {len(selected_items)}")
    
    print("\nExtracting acoustic features in parallel...")
    rows = []
    skipped = 0
    
    # Use max_workers=6 for responsive CPU processing
    with ProcessPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(process_single_audio, item): item for item in selected_items}
        count = 0
        for future in as_completed(futures):
            res = future.result()
            count += 1
            if res is not None:
                rows.append(res)
            else:
                skipped += 1
            if count % 100 == 0 or count == len(selected_items):
                print(f"Extracted features for {count}/{len(selected_items)} stammer files (valid: {len(rows)}, skipped: {skipped})")
                
    df_stammer = pd.DataFrame(rows)
    print(f"\nStammer feature dataframe shape: {df_stammer.shape}")
    
    # Load existing features.csv
    features_csv = "features.csv"
    if os.path.exists(features_csv):
        df_old = pd.read_csv(features_csv)
        print(f"Existing features.csv shape: {df_old.shape}")
        
        # Filter out any prior stammer entries if present to avoid duplicates
        df_old_clean = df_old[df_old["disorder_type"] != "stammer"].copy()
        
        # Save backup
        df_old.to_csv("features_backup.csv", index=False)
        print("Created backup: features_backup.csv")
        
        df_combined = pd.concat([df_old_clean, df_stammer], ignore_index=True)
    else:
        df_combined = df_stammer
        
    df_combined.to_csv(features_csv, index=False)
    print(f"\nSuccessfully updated {features_csv}!")
    print(f"Total dataset shape: {df_combined.shape}")
    print("\nClass distribution across 3 fields:")
    print(df_combined["disorder_type"].value_counts())
    print("\nUnique speakers count:", df_combined["speaker_id"].nunique())

if __name__ == "__main__":
    main()
