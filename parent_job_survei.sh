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
        return_message=`cat qsub_myjob.log`
        if [ "$return_message" == "ssh_exchange_identification: Connection closed by remote host" ]; then
            echo "`date +%Y/%m/%d-%H:%M:%S` : qstat returned "$return_message". continue surveillance." >> $logfilename
            sleep 1
            continue
        fi
        ret_code=`echo $?`
        if [ "$ret_code" = 0 ]; then
            ret=`cat qsub_myjob.log | awk NR==3 | awk '{print $5}'`
            # 終了検知
            if [ $ret = "C" ]; then
                echo "`date +%Y/%m/%d-%H:%M:%S` parent job ended. will stop child job(s), if still running." >> $logfilename
                for item in ${jobids[@]}
                do
                    # 子ジョブのステータスがRやQの時のみqdelする
                    ssh $MISYSTEM_HEADNODE_HOSTNAME qstat $item > qsub_childjob.log 2>&1
                    child_ret=`cat qsub_childjob.log | awk NR==3 | awk '{print $5}'`
                    if [ $child_ret = "C" ]; then
                        continue
                    fi
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
