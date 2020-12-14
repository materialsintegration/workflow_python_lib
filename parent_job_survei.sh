#!/bin/bash
#PBS -q ex_queue

if [ "$2" = "" ]; then
    echo "not define job id for stop"
    exit 1
fi

jobids=($2)

if [ "$1" = "" ]; then
    echo "not define job id for surveillance"
    exit 1
fi

cd $PBS_O_WORKDIR
myjob_id=$1
while [ 1 = 1 ]; 
do
    ssh $MISYSTEM_HEADNODE_HOSTNAME qstat $myjob_id > qsub_myjob.log 2>&1
    ret_code=`echo $?`
    if [ "$ret_code" = 0 ]; then
        ret=`cat qsub_myjob.log | awk NR==3 | awk '{print $5}'`
        # 終了検知
        if [ $ret = "C" ]; then
            echo "`date +%Y/%m/%d-%H:%M:%S` parent job ended. will stop femccv job(s)" >> execFemccv.log
            for item in ${jobids[@]}
            do
                echo "`date +%Y/%m/%d-%H:%M:%S` : ssh $MISYSTEM_HEADNODE_HOSTNAME qdel $item" >> execFemccv.log
                ssh $MISYSTEM_HEADNODE_HOSTNAME qdel $item
            done
            exit 1
        fi
    else
        # 終了コードが０以外だったら？
        echo "`date +%Y/%m/%d-%H:%M:%S` cannot get status of parent job($myjob_id)" >> execFemccv.log
        for item in ${jobids[@]}
        do
            echo "`date +%Y/%m/%d-%H:%M:%S` parent job dead?. will stop femccv job(s)" >> execFemccv.log
            echo "`date +%Y/%m/%d-%H:%M:%S` : ssh $MISYSTEM_HEADNODE_HOSTNAME qdel $item" >> execFemccv.log
            ssh $MISYSTEM_HEADNODE_HOSTNAME qdel $item
        done
        exit 1
    fi
    sleep 10
done
