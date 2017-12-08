#!/usr/bin/env bash

# Break if any command fails
set -o errexit
set -o nounset

# make sure we early out if everything is already done
test -d ~ubuntu/_terminated && { echo "Toolchain already installed."; exit 0; }

# General setup of ML box as discussed in 2nd meeting
apt-get update
apt-get --yes upgrade  # comment out if you do not want to always have the latest versions

apt-get install -y python3-pip
#apt-get install -y default-jdk
apt-get install -y python3-tk

# python2? what's that?
sudo rm -rf /usr/bin/python
sudo ln -s -f /usr/bin/python3 /usr/bin/python
sudo ln -s -f /usr/bin/pip3 /usr/bin/pip
pip install --upgrade pip

# fix user ubuntu's password mess of ubuntu/xenial64 boxes
apt-get install -y expect
echo '#!/usr/bin/expect
  set timeout 20
  spawn sudo passwd ubuntu
  expect "Enter new UNIX password:" {send "ubuntu\\r"}
  expect "Retype new UNIX password:" {send "ubuntu\\r"}
  interact' > change_ubuntu_password
chmod +x change_ubuntu_password
./change_ubuntu_password

# XWindow stuff (set our display running on host (e.g. Win10 PC))
# 0=port 6000, 1=port 6001, etc..
echo "export DISPLAY=0:0" >> /home/ubuntu/.bashrc

# 20tab script to setup UE4 service
apt-get install dos2unix
cd /vagrant
chmod 0755 bootstrap-unreal.sh
# weird problem with 'bash\\M' not found (something wrong with the line endings)
dos2unix bootstrap-unreal.sh
sudo /vagrant/bootstrap-unreal.sh Engine2Learn
cd

# git the TensorFlowOnSpark code
cd ~ubuntu
rm -rf TensorFlowOnSpark
git clone https://github.com/yahoo/TensorFlowOnSpark.git
cd TensorFlowOnSpark
echo "export TFoS_HOME="$(pwd) >> /home/ubuntu/.bashrc
export TFoS_HOME=$(pwd)
cd
# give to ubuntu
sudo chown -R ubuntu:ubuntu /home/ubuntu/TensorFlowOnSpark

# Get Java
sudo apt-get --yes install openjdk-8-jre-headless
# store installation path: usually something like: /usr/lib/jvm/java-8-openjdk-amd64/
echo "export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64/" >> /home/ubuntu/.bashrc

# Get and install Hadoop
cd ~ubuntu
wget --no-verbose http://apache.osuosl.org/hadoop/common/hadoop-2.8.2/hadoop-2.8.2.tar.gz
mkdir hadoop
tar -xvf hadoop-2.8.2.tar.gz -C hadoop --strip-components=1
echo "export HADOOP_HOME=$(pwd)/hadoop" >> /home/ubuntu/.bashrc
export HADOOP_HOME=$(pwd)/hadoop
echo "export PATH=$PATH:$HADOOP_HOME/bin" >> /home/ubuntu/.bashrc
export PATH=$PATH:$HADOOP_HOME/bin
echo "export HADOOP_CLASSPATH=$(hadoop classpath)" >> /home/ubuntu/.bashrc
export HADOOP_CLASSPATH=$(hadoop classpath)
echo "export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop" >> /home/ubuntu/.bashrc
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
# Give to ubuntu
sudo chown -R ubuntu:ubuntu /home/ubuntu/hadoop

# Get Spark and Install
# replace with a current version of spark
cd ~ubuntu
wget --no-verbose http://archive.apache.org/dist/spark/spark-2.2.0/spark-2.2.0-bin-hadoop2.7.tgz
gunzip spark-2.2.0-bin-hadoop2.7.tgz
tar -xvf spark-2.2.0-bin-hadoop2.7.tar
rm spark-2.2.0-bin-hadoop2.7.tar
echo "export SPARK_HOME=$(pwd)/spark-2.2.0-bin-hadoop2.7" >> /home/ubuntu/.bashrc
export SPARK_HOME=$(pwd)/spark-2.2.0-bin-hadoop2.7
echo "export PATH=${SPARK_HOME}/bin:${PATH}" >> /home/ubuntu/.bashrc
export PATH=${SPARK_HOME}/bin:${PATH}
# give to ubuntu
sudo chown -R ubuntu:ubuntu ${SPARK_HOME}

# get Hadoop and install
#cd
#wget --no-verbose http://apache.mirror.iphh.net/hadoop/common/hadoop-2.7.4/hadoop-2.7.4.tar.gz
#gunzip hadoop-2.7.4.tar.gz
#tar -xvf hadoop-2.7.4.tar
#rm hadoop-2.7.4.tar

# link all python libs inside /vagrant/
echo "export PYTHONPATH=/vagrant/" >> /home/ubuntu/.bashrc
export PYTHONPATH=/vagrant/

# Setup of Apache Zeppelin incl. Apache Spark in local mode, as discussed in 3rd meeting
## To speed up operations, the zeppelin-0.7.2-bin-all.tgz can be downloaded upfront to the host OS folder which is mapped to the shared folder /vagrant inside the guest machine.
## If it is not already downloaded to /vagrant, download it now to that folder. As this folder is on the host, the downloaded file can be reused even after this box is destroyed.
#cd /vagrant
##sudo --user=ubuntu wget --no-verbose --timestamping http://www-eu.apache.org/dist/zeppelin/zeppelin-0.7.2/zeppelin-0.7.2-bin-all.tgz
## get apache spark
#sudo --user=ubuntu wget --no-verbose --timestamping https://d3kbcqa49mib13.cloudfront.net/spark-2.2.0-bin-hadoop2.7.tgz
## Always download the checksum, overwriting any previously downloaded file
#sudo --user=ubuntu wget --no-verbose --output-document=spark-2.2.0-bin-hadoop2.7.tgz.sha https://www.apache.org/dist/spark/spark-2.2.0/spark-2.2.0-bin-hadoop2.7.tgz.sha
## Compare checksum
##sudo --user=ubuntu sha512sum -c spark-2.2.0-bin-hadoop2.7.tgz.sha spark-2.2.0-bin-hadoop2.7.tgz
#cd /home/ubuntu
#sudo --user=ubuntu tar --extract --skip-old-files --file /vagrant/spark-2.2.0-bin-hadoop2.7.tgz
#sudo --user=ubuntu ln --symbolic --force /home/ubuntu/spark-2.2.0-bin-hadoop2.7 /home/ubuntu/spark

# install important python libs
sudo apt-get install -y python-numpy python-dev cmake zlib1g-dev libjpeg-dev xvfb libav-tools xorg-dev python-opengl libboost-all-dev libsdl2-dev swig
sudo pip install tensorflow
sudo pip install tensorflowonspark
sudo pip install dm-sonnet
sudo pip install jupyter notebook
sudo pip install pyspark
sudo pip install cached_property
sudo pip install numpy
sudo pip install scipy
sudo pip install pydevd
sudo pip install cython
sudo pip install matplotlib
sudo pip install pygame
sudo pip install msgpack-python
sudo pip install msgpack-numpy
sudo pip install pillow
sudo pip install gym
sudo pip install gym[atari]

## get openAI gym (including Atari Envs)
#cd ~ubuntu
#rm -rf gym
#git clone https://github.com/openai/gym.git
#cd gym/
#sudo pip install --user -e .
#sudo pip install --user -e '.[atari]'
## Give to ubuntu
#sudo chown -R ubuntu:ubuntu /home/ubuntu/gym
#cd
## get the Arcade Learning Env
#cd ~ubuntu
#git clone https://github.com/mgbellemare/Arcade-Learning-Environment.git
## install its dependencies
#sudo apt-get install -y libsdl1.2-dev libsdl-gfx1.2-dev libsdl-image1.2-dev cmake
#mkdir build && cd build
#cmake -DUSE_SDL=ON -DUSE_RLGLUE=OFF -DBUILD_EXAMPLES=ON ..
#make -j 4

# download MNIST data for example runs
#sudo mkdir ${TFoS_HOME}/mnist
#pushd ${TFoS_HOME}/mnist
#sudo curl -O "http://yann.lecun.com/exdb/mnist/train-images-idx3-ubyte.gz"
#sudo curl -O "http://yann.lecun.com/exdb/mnist/train-labels-idx1-ubyte.gz"
#sudo curl -O "http://yann.lecun.com/exdb/mnist/t10k-images-idx3-ubyte.gz"
#sudo curl -O "http://yann.lecun.com/exdb/mnist/t10k-labels-idx1-ubyte.gz"
#popd
#sudo chown -R ubuntu:ubuntu mnist

# Start Spark (master + n slaves)
pushd ${SPARK_HOME}
cp conf/spark-defaults.conf.template conf/spark-defaults.conf
cp conf/spark-env.sh.template conf/spark-env.sh
echo "SPARK_WORKER_INSTANCES=3" >> conf/spark-env.sh
echo "PYTHONPATH=/vagrant/" >> conf/spark-env.sh
echo "spark.master   spark://ubuntu-xenial:7077" >> conf/spark-defaults.sh
echo "spark.executor.instances  3" >> conf/spark-defaults.sh
popd

echo "export MASTER=spark://$(hostname):7077" >> /home/ubuntu/.bashrc
export MASTER=spark://$(hostname):7077
echo "export SPARK_WORKER_INSTANCES=3" >> /home/ubuntu/.bashrc
export SPARK_WORKER_INSTANCES=3
echo "export CORES_PER_WORKER=1" >> /home/ubuntu/.bashrc
export CORES_PER_WORKER=1
echo "export TOTAL_CORES=$((${CORES_PER_WORKER}*${SPARK_WORKER_INSTANCES}))" >> /home/ubuntu/.bashrc
${SPARK_HOME}/sbin/start-master.sh
${SPARK_HOME}/sbin/start-slave.sh -c $CORES_PER_WORKER -m 3G ${MASTER}

# make pyspark use python3, not 2
echo "export PYSPARK_PYTHON=python3" >> /home/ubuntu/.bashrc

## prep (unzip) MNIST data via Spark
#cd ${TFoS_HOME}
#sudo rm -rf examples/mnist/csv
#sudo ${SPARK_HOME}/bin/spark-submit --master ${MASTER} ${TFoS_HOME}/examples/mnist/mnist_data_setup.py --output examples/mnist/csv --format csv

## run the MNIST training via Spark
#sudo ${SPARK_HOME}/bin/spark-submit --master ${MASTER} --py-files ${TFoS_HOME}/examples/mnist/spark/mnist_dist.py --conf spark.cores.max=${TOTAL_CORES} --conf spark.task.cpus=${CORES_PER_WORKER} --conf spark.executorEnv.JAVA_HOME="$JAVA_HOME" ${TFoS_HOME}/examples/mnist/spark/mnist_spark.py --cluster_size ${SPARK_WORKER_INSTANCES} --images examples/mnist/csv/train/images --labels examples/mnist/csv/train/labels --format csv --mode train --model mnist_model

cd
mkdir _terminated
