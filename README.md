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

- Now Install Grafana with helm chart.
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
- Also create alert if one of the node is down
  ![alert detail](https://github.com/user-attachments/assets/f524926e-37a6-4841-a9f7-38cb53e999ff)


  
### Step-2.4 - Deploy Elasticsearch, Kibana, and fluent-bit on K8s for Kubernetes & application logging purposes.
- I deployed Elasticsearch, Kibana, and fluent-bit on my k8s cluster via Helm Chart. I edit their values.yaml according to my needs.Also you can check ecerything i created for EFK [EFK Stack Files](https://github.com/Lastroke/app/tree/develop/efk) Let me explain the steps: 
- I created 3 different PV for Elasticsearch because Elasticsearch is a clustered setup to provide redundancy, high availability, and scalability. And default is 3 pods.
- After that i changed the values.yaml. Heres what i changed [ES Values](https://github.com/Lastroke/app/blob/develop/efk/es-values.yaml):
  - To access Kibana with authentication i enabled xpack security under esConfig.
     ```yaml
        esConfig:
         elasticsearch.yml: |
            xpack.security.enabled: true
            xpack.monitoring.collection.enabled: true
    ```
  - To performance and stability for elasticsearch instances, i configure Heap Size
     ```yaml
        esJavaOpts: "-Xmx1g -Xms1g"
     ```
  - To bound PVC with my PV which it is already created, i need to also edit these part in values.yaml.
     ```yaml
     storageClassName: local-storage
     size: 2Gi
     ```
- After everything is set, install the chart with command:
    ```sh
    helm install elasticsearch elastic/elasticsearch -f es-values.yaml -n kube-logging
    ```
- Next is deploy the Kibana. For Kibana i only edit the values.yaml and install it
- Here is what i changed [Kibana Values](https://github.com/Lastroke/app/blob/develop/efk/kibana-values.yaml):
  - To expose the Kibana application outside of your Kubernetes cluster: 
     ```yaml
        serviceType: NodePort
        nodePort: 30005
    ```
  - Because Authenticaiton is enabled for Kibana i gave service account token and password for elastic as Env variables to Kibana. After Elastic 8 username part is no more used. To configure it service token is needed. Thats why icreate service token for user.
     ```yaml
         extraEnvs:
            - name: ELASTICSEARCH_SERVICE_ACCOUNT_TOKEN
            valueFrom:
              secretKeyRef:
                name: kibana-sa-token
                key: token
          - name: ELASTICSEARCH_PASSWORD
            valueFrom:
              secretKeyRef:
                name: kibana-secret
                key: password
    ```
  - I configure Kibana config to use right host and data to connect Elasticsearch
     ```yaml
        kibanaConfig: 
          kibana.yml: |
            server.host: "0.0.0.0"
            elasticsearch.hosts: ["http://elasticsearch-master:9200"]
            elasticsearch.serviceAccountToken: "${ELASTICSEARCH_SERVICE_ACCOUNT_TOKEN}"
            elasticsearch.password: "${ELASTICSEARCH_PASSWORD}"
     ```
- After everything is set, install the chart with command:
    ```sh
        helm install kibana elastic/kibana -n kube-logging -f kibana-values.yaml
    ```
    ![elastic giriş ekranı](https://github.com/user-attachments/assets/f19150f4-e5b9-4702-a2aa-c387d8d3527a)
    - Here you can see auth method is enabled and can log in.
    ![Ekran görüntüsü 2024-08-13 161033](https://github.com/user-attachments/assets/fc40d1a4-1ef5-43dc-9c81-77537f8ac154)
    - And log index you can see
    ![image](https://github.com/user-attachments/assets/817bf7fd-64e9-43d8-934c-e42890375b83)
    ![elastic fluent](https://github.com/user-attachments/assets/df1df0a2-5bf8-4a53-b804-6538a736d7a7)




- Next is to deploy Fluent-bit and also configuring our application logs according to task.
- Here is what i changed [Fluent Values](https://github.com/Lastroke/app/blob/develop/efk/fluent-values.yaml):
  - I added 2 extra config in fluentbit values.yaml. First is a second Input for my application logs. So that when application is run fluentbit take logs from /var/log/egejavaapp/*.json. Second Part is for OUTPUT i just gave user, password, host so it can connect to Elastic.
     ```yaml
        inputs: |
            ..... default config
            [INPUT]
                Name              tail
                Tag               java-app.*
                Path              /var/log/egejavaapp/*.json
                Parser            json
                DB                /var/log/flb_java_app.db
                Mem_Buf_Limit     5MB
                Skip_Long_Lines   On
                Refresh_Interval  10
     ...... default config
     outputs: |
        [OUTPUT]
            Name            es
            Match           *
            Host            elasticsearch-master
            Port            9200
            HTTP_User       elastic
            HTTP_Passwd     ******
            Logstash_Format On
            Logstash_Prefix egeindex
            Replace_Dots    On
            Suppress_Type_Name On
            tls On
            tls.verify Off
            Retry_Limit     False
    ```
  - Here i also give my application log folder as a volume to fluent-bit pod so it can read and upload to Elastic. 
     ```yaml
         daemonSetVolumes:
           ... default config
          - name: log-volume
            emptyDir: {}
         daemonSetVolumeMounts:
             ..... default config
         - name: log-volume
           mountPath: /var/log/egejavaapp
           readOnly: true
    ```
  - After everything is set, install the chart with command:
    ```sh
        helm install fluent-bit fluent/fluent-bit -n kube-logging -f fluent-values.yaml
    ```
- And here we can see fluentbit pod logs
  ![image](https://github.com/user-attachments/assets/ef811a9a-6abb-4628-8aa7-53bb84e9471b)

- Here how i configured my application to create logs
    - to a file asynchronously
    - Log file size should not be greater than 1GB
    - Log files should be rotated daily
  - I create logback.xml in src/main/resources [Logback File](https://github.com/Lastroke/app/blob/develop/src/main/resources/logback.xml):
    - Here you can see that my log folder that i also mount the application and to Fluent-bit. I use dd-MM-yyyy for daily rotation and total size 1GB. At the I added AsyncAppender so logs will be written asynchronously
      ```xml
          ...
           <file>/var/log/egejavaapp/application.json</file>
          ...
          <fileNamePattern>/var/log/egejavaapp/application.%d{dd-MM-yyyy}.json</fileNamePattern>
          ...
          <totalSizeCap>1GB</totalSizeCap>

          <appender name="ASYNC_JSON_FILE" class="ch.qos.logback.classic.AsyncAppender">
              <appender-ref ref="JSON_FILE"/>
              .....
      ```
    - I added dependencies to my [Pom XML](https://github.com/Lastroke/app/blob/develop/pom.xml) so that logback can run without failure.

- Now i set logback and also give necessary information to take log to Fluent-bit. My application logs will be in Elastic daily with max size 1GB and will be written asynchronously for performance
  - Fluentbit successfully take the logs from my application log folder
    ![fluentbit pod logs önemli](https://github.com/user-attachments/assets/672aaefe-014f-44d1-8954-95d27fa8f106)

  - And Here you can see the index and you can see that its daily
      ![çok önemli,](https://github.com/user-attachments/assets/3b82b7f1-fa1b-42b2-8bfa-a300dc929cf6)


## Step-3

### Step-3.1
- I created the necessary manifest files for Java Application. Here you can check it.[Java App Manifest Files](https://github.com/Lastroke/app/tree/develop/java-app)
- Metrics Server is installed via Helm for HPA to work properly
   ```sh
        helm install metrics-server metrics-server/metrics-server
    ```
- Nginx Ingress Controller is installed via Helm for Ingress Resource. Here i set the service type to NodePort because there is no LoadBalancer setup in my environment.
    ```sh
        helm install ingress-nginx ingress-nginx/ingress-nginx --set controller.service.type=NodePort
    ```
- In my [Ingress Manifest](https://github.com/Lastroke/app/blob/develop/java-app/ingress.yaml) i set ingress class name to nginx. Its default name from Nginx Controller.
  ```yaml
      ingressClassName: nginx
  ```
- Every Manifest file is set and ready to use.
### Step-3.2
- So lets take look at closer to my [Deployment Manifest](https://github.com/Lastroke/app/blob/develop/java-app/deployment.yaml)
  - As requested from the task replica is set to 4 and in order to make sure pods are distributed equally across nodes podAntiAffinity is used. Why i choose preferred and not required because if requiredDurinScheduling is use only to pod will placed to node-1 and node-2 then it wont schedule anymore because the two nodes get already 1 pod. Thats why i use preferred. I set to weight: 100 to let scheduler knows its very important. So with that configuration 2 pods will be in node-1 and 2 will be node-2.
      ```yaml
          affinity:
            podAntiAffinity:
              preferredDuringSchedulingIgnoredDuringExecution:
              - weight: 100
                podAffinityTerm:
                  labelSelector:
                    matchExpressions:
                    - key: app
                      operator: In
                      values:
                      - java-app
                  topologyKey: "kubernetes.io/hostname"
      ```
      ![java pp pods bunu kullan](https://github.com/user-attachments/assets/dcd3ba30-51d9-4d68-8983-d59def157f9e)

  - **readinessProbe** and **livenessProbe** are used or ensuring the application receives requests as soon as it is ready and restarted if there is a problem. If the readiness probe fails, Kubernetes will not route any traffic to that container. If the liveness probe fails, Kubernetes will restart the container
  ```yaml
      readinessProbe:
          httpGet:
            path: /api/foos?val=egeuzma
            port: 9001
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /api/foos?val=egeuzma
            port: 9001
          initialDelaySeconds: 15
          periodSeconds: 20
  ```
  - And for application log which i already configuren in logback.xml, i give as a volumeMount.
  ```yaml
      volumeMounts:
        - name: log-volume
          mountPath: /var/log/egejavaapp
      volumes:
      - name: log-volume
        emptyDir: {}
  ```
### Step-3.3

### Step-3.4

### Step-3.5


## Step-4
