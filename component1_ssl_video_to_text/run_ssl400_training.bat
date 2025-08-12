@echo off
echo Starting SSL400 Training...
echo Using Python environment: D:/shanuka git/SSL-Assistive-Tool/.venv/Scripts/python.exe
echo Current directory: %CD%

"D:/shanuka git/SSL-Assistive-Tool/.venv/Scripts/python.exe" src\train.py ^
    --train_data_path "data\ssl400\train" ^
    --val_data_path "data\ssl400\val" ^
    --num_classes 383 ^
    --experiment_name "ssl400_training" ^
    --batch_size 8 ^
    --epochs 50 ^
    --sequence_length 60 ^
    --learning_rate 0.001 ^
    --sequence_model lstm ^
    --pretrained_backbone

echo Training completed. Check logs above for results.
pause
