import pandas as pd
import numpy as np
import tempfile
import os
import soundfile as sf
from feature_extraction import extract_extended_features

try:
    from datasets import load_dataset
except ImportError:
    print("datasets package not installed. Skipping stammer extraction.")
    exit(0)

def main():
    print("Loading SEP-28k stammer dataset from HuggingFace...")
    try:
        ds = load_dataset("isabelarvelo/sep28k-train-3-second-clips", split="train")
    except Exception as e:
        print(f"Failed to load dataset: {e}")
        return
        
    print(f"Dataset loaded. Total clips: {len(ds)}")
    
    features_list = []
    # Process up to 300 samples to balance with dysarthria/typical
    max_samples = 300
    count = 0
    
    for i, item in enumerate(ds):
        if count >= max_samples:
            break
            
        audio = item.get("audio")
        if not audio:
            continue
            
        y = audio["array"]
        sr = audio["sampling_rate"]
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
            
        try:
            sf.write(temp_path, y, sr)
            features = extract_extended_features(temp_path)
            
            if features is not None:
                row = {}
                for j in range(13):
                    row[f"mfcc_{j+1}"] = features[j]
                    row[f"mfcc_delta_{j+1}"] = features[13+j]
                    row[f"mfcc_delta2_{j+1}"] = features[26+j]
                    
                row["pitch_mean"] = features[39]
                row["pitch_std"] = features[40]
                row["zcr_mean"] = features[41]
                row["zcr_std"] = features[42]
                
                row.update({
                    "speaker_id": f"stammer_{i}", 
                    "gender": "unknown",
                    "disorder_type": "stammer",
                    "severity": "unknown",
                    "audio_path": "huggingface_dataset"
                })
                
                features_list.append(row)
                count += 1
                
                if count % 50 == 0:
                    print(f"Processed {count} stammer samples...")
                    
        except Exception as e:
            pass # Ignore single item errors
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    if features_list:
        print(f"Appending {len(features_list)} stammer samples to features.csv...")
        df_new = pd.DataFrame(features_list)
        df_old = pd.read_csv("features.csv")
        df_combined = pd.concat([df_old, df_new], ignore_index=True)
        df_combined.to_csv("features.csv", index=False)
        print("Done!")
    else:
        print("No stammer features extracted.")

if __name__ == "__main__":
    main()
