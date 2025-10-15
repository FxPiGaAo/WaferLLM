./run_wse3.sh 32 1024 1024 4 false | tee -a log/wse3_gemv_32_1024_1024_4.log
./run_wse3.sh 64 1024 1024 8 false | tee -a log/wse3_gemv_64_1024_1024_8.log
./run_wse3.sh 128 1024 1024 8 false | tee -a log/wse3_gemv_128_1024_1024_8.log

./run_wse3.sh 32 2048 2048 4 false | tee -a log/wse3_gemv_32_2048_2048_4.log
./run_wse3.sh 64 2048 2048 8 false | tee -a log/wse3_gemv_64_2048_2048_8.log
./run_wse3.sh 128 2048 2048 8 false | tee -a log/wse3_gemv_128_2048_2048_8.log

./run_wse3.sh 64 4096 4096 8 false | tee -a log/wse3_gemv_64_4096_4096_8.log
./run_wse3.sh 128 4096 4096 8 false | tee -a log/wse3_gemv_128_4096_4096_8.log