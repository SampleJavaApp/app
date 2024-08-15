pipeline {
    agent {
        label 'jenkins-jenkins-agent'
    }
    environment {
        DOCKERHUB_REPO = 'egeuzma1/java-app'
        GIT_REPO_URL = 'github.com/Lastroke/app.git'
        GIT_BRANCH = 'develop'
    }
    stages {
        stage('Checkout') {
            steps {
                script {
                    try {
                        withCredentials([usernamePassword(credentialsId: 'github_credentials', usernameVariable: 'GITHUB_USERNAME', passwordVariable: 'GITHUB_PASSWORD')]) {
                            git branch: "${GIT_BRANCH}",
                                url: "https://${GITHUB_USERNAME}:${GITHUB_PASSWORD}@${GIT_REPO_URL}"
                        }
                    } catch (Exception e) {
                        currentBuild.result = 'FAILURE'
                        echo "Error during Git checkout: ${e.message}"
                        error "Stopping pipeline due to checkout failure."
                    }
                }  
            }
        }
        podTemplate(yaml: '''
              kind: Pod
              spec:
                containers:
                - name: kaniko
                  image: gcr.io/kaniko-project/executor:v1.6.0-debug
                  imagePullPolicy: Always
                  command:
                  - sleep
                  args:
                  - 99d
                  volumeMounts:
                    - name: dockerhub-secret
                      mountPath: /kaniko/.docker
                volumes:
                - name: dockerhub-secret
                  projected:
                    sources:
                    - secret:
                        name: dockerhub-secret
                        items:
                          - key: .dockerconfigjson
                            path: config.json
        '''
            ) {
                node(POD_LABEL) {
                    stage('Build with Kaniko') {
                        git 'https://github.com/jenkinsci/docker-inbound-agent.git'
                        container('kaniko') {
                            sh '/kaniko/executor -f `pwd`/Dockerfile -c `pwd` --insecure --skip-tls-verify --cache=true --destination=mydockerregistry:5000/myorg/myimage'
                        }
                    }
                }
        }
        // stage('Build and Push Docker Image') {
        //     steps {
        //         container('kaniko') {
        //             script {
        //                 sh '''
        //                 /kaniko/executor \
        //                     --context `pwd` \
        //                     --dockerfile `pwd`/Dockerfile \
        //                     --destination=${DOCKERHUB_REPO}:v$BUILD_NUMBER \
        //                     --cleanup
        //                 '''
        //             }
        //         }
        //     }
        // }
    }
    post {
        success {
            echo 'Docker image built and pushed successfully.'
        }
        failure {
            echo 'Docker image build or push failed.'
        }
    }
}
