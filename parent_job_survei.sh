#!/bin/bash
#PBS -q ex_queue
#PBS -l nodes=1:non-calc-node

check_parent_job() {
    if [ "$1" = "" ]; then
        echo "not define parent job id for surveillance"
        exit 1
    fi
    
    myjob_id=$1
    shift
    
    if [ "$1" = "" ]; then
        echo "not define log file name"
        exit 1
    fi
    
    logfilename=$1
    echo "logfilename = $logfilename" >> $logfilename
    echo "myjob_id = $myjob_id" >> $logfilename
    shift
    
    if [ "$1" = "" ]; then
        echo "not define id for children for parent id"
        exit 1
    fi
    
    jobids=($@)
    echo "job ids = ${jobids[@]}" >> $logfilename

    cd $PBS_O_WORKDIR
    while [ 1 = 1 ]; 
    do
        ssh $MISYSTEM_HEADNODE_HOSTNAME qstat $myjob_id > qsub_myjob.log 2>&1
        ret_code=`echo $?`
        if [ "$ret_code" = 0 ]; then
            ret=`cat qsub_myjob.log | awk NR==3 | awk '{print $5}'`
            # 終了検知
            if [ $ret = "C" ]; then
                echo "`date +%Y/%m/%d-%H:%M:%S` parent job ended. will stop child job(s)" >> $logfilename
                for item in ${jobids[@]}
                do
                    echo "`date +%Y/%m/%d-%H:%M:%S` : ssh $MISYSTEM_HEADNODE_HOSTNAME qdel $item" >> $logfilename
                    ssh $MISYSTEM_HEADNODE_HOSTNAME qdel $item
                done
                exit 1
            fi
        else
            # 終了コードが０以外だったら？
            echo "`date +%Y/%m/%d-%H:%M:%S` cannot get status of parent job($myjob_id)" >> $logfilename
            for item in ${jobids[@]}
            do
                echo "`date +%Y/%m/%d-%H:%M:%S` parent job dead? stop child job(s)" >> $logfilename
                echo "`date +%Y/%m/%d-%H:%M:%S` : ssh $MISYSTEM_HEADNODE_HOSTNAME qdel $item" >> $logfilename
                ssh $MISYSTEM_HEADNODE_HOSTNAME qdel $item
            done
            exit 1
        fi
        sleep 10
    done
}

check_parent_job $@
