# Ege Uzma Devops Engineering Study

- Hello, in this documentation i will try to  explain what i did and how i did to complete this case.

- Note: I added Step-4 questions answers to this README file at the bottom.

## Step-1

### Step-1.1 Fork the Repository

- I forked this [sample-java-app](https://github.com/SampleJavaApp/app) to my own GitHub account and started to work on develop branch.

### Step-1.2 Create a Dockerfile for the application using multi-stage builds

- I created a Dockerfile with multi-stages for this application.

    - For build stage in Dockerfile i choose eclipse-temurin:11-jdk-focal because Eclipse Temurin is a popular, well-maintained OpenJDK distribution. The JDK version is used here because we need compilation tools for the build process.

        ```Dockerfile
            FROM eclipse-temurin:11-jdk-focal AS build
        ```

    - Then The working directory for the application is defined. All files within this java-app project are copied to the directory specified in the image.

        ```Dockerfile
            WORKDIR /app
            COPY . .
        ```
    - The execute permission is granted to Maven Wrapper. This will able to build our app in Jenkins env. After permission i used mvnw to build and package the java application. There are 2 main reason why i choose to do that.
        - The Maven Wrapper ensures that everyone uses the same version of Maven. So that there will be no build failure or inconsistencies
        - With mvnw, we don't need to have Maven installed globally on our machine or on our CI/CD environment. It uses the wrapper scripts.
            ```Dockerfile
            RUN chmod +x mvnw
            RUN ./mvnw clean package -DskipTests
            ```
    - Next is to run already compiled application in previous stage. I used the JRE version in the build as we only need to run the compiled application, not build it. This results in a smaller final image. 

        ```Dockerfile
            FROM eclipse-temurin:11-jre-focal
        ```
    - Because this stage is for runtime, other files except JAR file are not needed. Only JAR file is copied.
    
        ```Dockerfile
            COPY --from=build /app/target/app-0.0.1-SNAPSHOT.jar ./app.jar
        ```
    - Last but not least, According to application.properties file, I exposed the application to 9001 port and execute the JAR. 

        ```Dockerfile
            EXPOSE 9001
            CMD ["java", "-jar", "app.jar"]
        ```
- Here is the [Dockerfile](https://github.com/Lastroke/app/blob/develop/Dockerfile)

## Step-2

### Step-2.1 - Create a Production Ready Kubernetes Cluster

- First I setup the kubernetes cluster to my own PC with Vagrant file you provided but later i had some issues with PC resources. That is why i setup k8s cluster again in GCP.

- I created 3 VM in GCP and named them as k8s-master, node-1 (worker) and node-2 (worker).
  ![image](https://github.com/user-attachments/assets/ed034c68-af53-417b-811c-3e85cf87a098)

- I create firewall rules for k8s components on master and worker nodes. Such as Kubelet, Kubernetes API, etcd, NodePort (workers only)

- So next step is to setup container runtime for our nodes.
- But before setup container runtime there are prerequisites for it. Forwarding IPv4 and letting iptables see bridged traffic.
    - First we need to load 2 modules in linux for storage driver and bridge networking.
    ```sh
    modprobe overlay #storage driver
    modprobe br_netfilter # nat for bridge networking
    ```
    - Forwarding IPv4 and letting iptables see bridged traffic. /etc/sysctl.d/k8s.conf file is edited.
    ```sh
    net.bridge.bridge-nf-call-ip6tables = 1
    net.bridge.bridge-nf-call-iptables = 1
    net.ipv4.ip_forward = 1
    ```
    - And finally system restart
    ```sh
    sudo sysctl --system
    ```
- Now we can install container runtime containerd. Because Docker has no support anymore and containerd was actually responsible for the core container operations in Docker. So i choose containerd as a container runtime for my nodes.
  - First Setup Docker's apt repository.
  ```sh
    sudo apt-get update
    sudo apt-get install ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc
  
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
  ```
  
  - Then install the containerd with apt-get
    ```sh
    sudo apt-get install containerd.io
    ```
- Kubelet and container runtime need to interact with Cgroup drivers in order to enforce resource management for pods and containers. And both needs to use same Cgroup driver. Because our init system use systemd we configure /etc/containerd/config.toml to use also systemd as a Cgroup driver and restart containerd.
    ```sh
    [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]
      [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
        SystemdCgroup = true
    ```
    ```sh
    sudo systemctl restart containerd
    ```
- Note: No need for Kubelet because its already set systemd in kubernetes v1.30

- Now it is turn for installing kubeadm, kubelet and kubectl.
  ```sh
    sudo apt-get update
    sudo apt-get install -y apt-transport-https ca-certificates curl gpg
    curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
    echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
    sudo apt-get update
    sudo apt-get install -y kubelet kubeadm kubectl
    sudo apt-mark hold kubelet kubeadm kubectl
    sudo systemctl enable --now kubelet
  ```
- Its time for creating the cluster now with kubeadm init in master node. Because i will use Calico as Networking, i set -pod-network-cidr=192.168.0.0/16.
    ```sh
    sudo kubeadm init --pod-network-cidr=192.168.0.0/16 --apiserver-advertise-address=10.156.0.2
    ```
- Create for user kubeconfig file to connect k8s cluster
    ```sh
    mkdir -p $HOME/.kube
    sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
    sudo chown $(id -u):$(id -g) $HOME/.kube/config
    export KUBECONFIG=$HOME/.kube/config
    ```
- Now its time to deploy pod network on master node and for that Calico will be used. Its popular and it provide robust networking features, strong security, and flexibility.
    ```sh
    kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.28.1/manifests/tigera-operator.yaml
    kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.28.1/manifests/custom-resources.yaml
    ```
- Final lets worker nodes join the k8s cluster with using kubeadm join
    ```sh
    kubeadm join 10.156.0.2:6443 --token ******** --discovery-token-ca-cert-hash sha256:*****
    ```
### Step-2.2 - Deploy Jenkins

- I setup Jenkins in jenkins-helm namespace on my k8s cluster via Helm.
- I created Persistent Volume for Jenkins. So that when i helm install PVC of Jenkins can claim it.
- Before creating PV i also create StorageClass named as local-storage.
- Here you can find the PV for Jenkins [Jenkins PV](https://github.com/Lastroke/app/blob/develop/jenkins/jenkins-pv.yaml)
- I didnt use default values.yaml because i need to configure it to my purpose. So here is what i changed in values.yaml
  - To expose the Jenkins application outside of your Kubernetes cluster: 
     ```yaml
    serviceType: NodePort
    nodePort: 30015
    ```
    
    Note: Also ingress controller and resource can be used for the same purposes. For that change service type to ClusterIP.
    
  - I changed nodeSelector to deploy Jenkins on worker node-2 as it requested. Because it was an basic 
expression, i didnt use podAffinty feature.
    Note: Worker node-2 also labeled deploy: jenkins.
    ```yaml
     nodeSelector:
          deploy: jenkins
    ```
  - To bound PVC with my PV which it is already created, i need to also edit these part in values.yaml.
     ```yaml
     storageClass: local-storage
     size: "10Gi"
     ```
  - After These all are set, i run helm istall command to deploy Jenkins on k8s cluster with my values.yaml  [Jenkins Values](https://github.com/Lastroke/app/blob/develop/jenkins/jenkins-values.yaml)
      ```sh
        helm install jenkins jenkins/jenkins -n jenkins-helm -f jenkins-helm.yaml
      ```
- With using externalIP:30015 i can access Jenkins and contiune to setup.
  ![jenkins](https://github.com/user-attachments/assets/53df83e9-bb7b-4d43-87e3-1bea03220cf5)
- After setup is finished and configured i can finally login with my username and password.
  ![image](https://github.com/user-attachments/assets/9353ed0a-4e16-4d97-b20d-bd8de575bb7a)



### Step-2.3 - Deploy Prometheus & Grafana on K8s for Kubernetes and application monitoring purposes
- Just like Jenkins, i also use Helm Charts to deploy Prometheus and Grafana.
- First i created 2 PV for prometheus-server itself and prometheus-alert. So that when i install the chart it will automatically bound.
- I also changed couple of things in the values.yaml. Here is what i changed.  [Prometheus Values And PV](https://github.com/Lastroke/app/tree/develop/prometheus)
  - To expose the Prometheus application outside of your Kubernetes cluster: 
     ```yaml
    serviceType: NodePort
    nodePort: 32090
    ```
  - To bound PVC with my PV which it is already created, i need to also edit these part in values.yaml.
     ```yaml
     storageClass: local-storage
     ```
- After everything is set, install the chart with command:
  ```sh
    helm install prometheus prometheus-community/prometheus -f prometheus-values.yaml
  ```
  ![Ekran görüntüsü 2024-08-10 203548](https://github.com/user-attachments/assets/248d928c-589a-4866-afce-5c52c7fa9801)

- Now Install Grafana with helm charts.
- Just like in prometheus, i also create a PV for Grafana. So that when i install the chart it will automatically bound.
- I also changed couple of things in the values.yaml. Here is what i changed. [Grafana Values And PV](https://github.com/Lastroke/app/tree/develop/grafana)
    - To expose the Grafana application outside of your Kubernetes cluster: 
         ```yaml
        serviceType: NodePort
        nodePort: 32091
        ```
  - To bound PVC with my PV which it is already created, i need to also edit these part in values.yaml.
     ```yaml
     enabled: true
     storageClassName: local-storage
     ```
- After everything is set, install the chart with command:
    ```sh
    helm install my-grafana grafana/grafana -f grafana-values.yaml
    ```
- After i login the Grafana with username and password.  I set Prometheus as data source and create common dashboard.
  ![Ekran görüntüsü 2024-08-11 014500](https://github.com/user-attachments/assets/c4879314-fca3-4c0a-a2cc-a50a202bad8d)

  
### Step-2.4 - Deploy Elasticsearch, Kibana, and fluent-bit on K8s for Kubernetes & application logging purposes.



## Step-3

## Step-4
