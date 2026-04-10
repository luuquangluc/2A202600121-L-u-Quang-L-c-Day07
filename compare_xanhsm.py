import os
import json
from src.chunking import ChunkingStrategyComparator

def run_comparison():
    data_dir = "data_XanhSM"
    files_to_compare = [
        "ĐIỀU KHOẢN CHUNG.txt",
        "nhahang.txt",
        "khach_hang.txt"
    ]
    
    comparator = ChunkingStrategyComparator()
    all_results = {}
    
    print(f"{'File':<40} | {'Strategy':<15} | {'Count':<7} | {'Avg Length':<10}")
    print("-" * 80)
    
    for filename in files_to_compare:
        file_path = os.path.join(data_dir, filename)
        if not os.path.exists(file_path):
            print(f"Skipping {filename}: File not found")
            continue
            
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
            
        results = comparator.compare(text, chunk_size=500)
        all_results[filename] = results
        
        for strategy, stats in results.items():
            try:
                print(f"{filename[:38]:<40} | {strategy:<15} | {stats['count']:<7} | {stats['avg_length']:<10}")
            except UnicodeEncodeError:
                # Fallback for console that doesn't support Vietnamese characters
                safe_name = filename.encode('ascii', 'ignore').decode('ascii')
                print(f"{safe_name[:38]:<40} | {strategy:<15} | {stats['count']:<7} | {stats['avg_length']:<10}")

if __name__ == "__main__":
    run_comparison()
