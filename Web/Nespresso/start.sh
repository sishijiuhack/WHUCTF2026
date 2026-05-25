if [ -n "$GZCTF_FLAG" ]; then
  export FLAG="$GZCTF_FLAG"
else
  export FLAG="flag{Test_flag}"
fi

echo $FLAG | tee /flag
java -jar app.jar