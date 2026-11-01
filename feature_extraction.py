import os
import glob
import librosa
import numpy as np
import pandas as pd
import re
import noisereduce as nr

DATA_DIR = "torgo_data"
OUTPUT_FILE = "features.csv"

def get_severity(speaker_id, is_dysarthria):
    if not is_dysarthria:
        return "typical"
    
    mapping = {
        "F01": "severe", "M01": "severe", "M02": "severe", "M04": "severe",
        "M05": "moderate-severe",
        "F03": "moderate",
        "F04": "mild", "M03": "mild"
    }
    return mapping.get(speaker_id, "unknown")

def clean_audio(y, sr):
    y_trimmed, _ = librosa.effects.trim(y, top_db=25)
    if len(y_trimmed) == 0:
        return y_trimmed
    y_denoised = nr.reduce_noise(y=y_trimmed, sr=sr, stationary=False)
    y_norm = librosa.util.normalize(y_denoised)
    return y_norm

def extract_extended_features(audio_path):
    try:
        y, sr = librosa.load(audio_path, sr=16000, mono=True)
        y_cleaned = clean_audio(y, sr)
        if len(y_cleaned) == 0:
            return None
            
        # 1. MFCCs (13)
        mfccs = librosa.feature.mfcc(y=y_cleaned, sr=sr, n_mfcc=13)
        
        # 2. Delta and Delta-Delta MFCCs (13+13=26)
        delta_mfccs = librosa.feature.delta(mfccs)
        delta2_mfccs = librosa.feature.delta(mfccs, order=2)
        
        # Means
        mfccs_mean = np.mean(mfccs, axis=1)
        delta_mfccs_mean = np.mean(delta_mfccs, axis=1)
        delta2_mfccs_mean = np.mean(delta2_mfccs, axis=1)
        
        # 3. Pitch (fundamental frequency F0)
        f0 = librosa.yin(y_cleaned, fmin=50, fmax=500)
        f0_valid = f0[~np.isnan(f0)]
        pitch_mean = np.mean(f0_valid) if len(f0_valid) > 0 else 0.0
        pitch_std = np.std(f0_valid) if len(f0_valid) > 0 else 0.0
        
        # 4. Zero Crossing Rate
        zcr = librosa.feature.zero_crossing_rate(y_cleaned)
        zcr_mean = np.mean(zcr)
        zcr_std = np.std(zcr)
        
        features = np.concatenate([
            mfccs_mean,
            delta_mfccs_mean,
            delta2_mfccs_mean,
            [pitch_mean, pitch_std, zcr_mean, zcr_std]
        ])
        
        return features
    except Exception as e:
        print(f"Error processing {audio_path}: {e}")
        return None

def main():
    features_list = []
    folder_counts = {}
    skipped_count = 0
    
    categories = [
        "dysarthria_female", "dysarthria_male",
        "non_dysarthria_female", "non_dysarthria_male"
    ]
    
    for category in categories:
        folder_path = os.path.join(DATA_DIR, category)
        if not os.path.exists(folder_path):
            print(f"Warning: {folder_path} does not exist.")
            continue
            
        is_dysarthria = 1 if "non_dysarthria" not in category else 0
        gender = "female" if "female" in category else "male"
        
        wav_files = glob.glob(os.path.join(folder_path, "**", "*.wav"), recursive=True)
        folder_counts[category] = 0
        
        for idx, file_path in enumerate(wav_files):
            file_name = os.path.basename(file_path)
            speaker_id = "unknown"
            if "F0" in file_name or "M0" in file_name or "FC" in file_name or "MC" in file_name:
                match = re.search(r'([FM]C?0\d)', file_name)
                if match:
                    speaker_id = match.group(1)
                else:
                    path_match = re.search(r"([FM]\d+)", file_path)
                    speaker_id = path_match.group(1) if path_match else "unknown"
                
            severity = get_severity(speaker_id, is_dysarthria)
            
            features_extracted = extract_extended_features(file_path)
            if features_extracted is None:
                skipped_count += 1
                continue
                
            row = {}
            for i in range(13):
                row[f"mfcc_{i+1}"] = features_extracted[i]
                row[f"mfcc_delta_{i+1}"] = features_extracted[13+i]
                row[f"mfcc_delta2_{i+1}"] = features_extracted[26+i]
                
            row["pitch_mean"] = features_extracted[39]
            row["pitch_std"] = features_extracted[40]
            row["zcr_mean"] = features_extracted[41]
            row["zcr_std"] = features_extracted[42]
            
            row.update({
                "speaker_id": speaker_id,
                "gender": gender,
                "disorder_type": "dysarthria" if is_dysarthria == 1 else "typical",
                "severity": severity,
                "audio_path": file_path
            })
            
            features_list.append(row)
            folder_counts[category] += 1
            
            if (idx + 1) % 100 == 0:
                print(f"Processed {idx + 1} files in {category}...")
                
    if not features_list:
        print("No features extracted. Ensure audio files exist in the specified folders.")
        return

    df = pd.DataFrame(features_list)
    df.to_csv(OUTPUT_FILE, index=False)
    print("\nExtraction Complete!")
    print(f"Features saved to {OUTPUT_FILE}")
    print("\nPer-folder counts:")
    for k, v in folder_counts.items():
        print(f"  {k}: {v}")
    print(f"Skipped files: {skipped_count}")

if __name__ == "__main__":
    main()
