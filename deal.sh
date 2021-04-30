for i in `ls strategy/`
do
    iconv -f gbk -t utf-8 strategy/$i  > strategy/${i%.*}.py
done
