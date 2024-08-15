pipeline {
    agent {
        label 'kaniko'
    }
    environment {
        DOCKERHUB_REPO = 'egeuzma1/java-app'
        GIT_REPO_URL = 'github.com/Lastroke/app.git'
        GIT_BRANCH = 'develop'
    }
    stages {
        // stage('Build with Kaniko') {
        //     environment {
        //         PATH = "/busybox:/kaniko:$PATH"
        //     }
        //     steps {
        //         withCredentials([usernamePassword(credentialsId: 'github_credentials', usernameVariable: 'GITHUB_USERNAME', passwordVariable: 'GITHUB_PASSWORD')]) {
        //             git branch: "${GIT_BRANCH}",
        //                 url: "https://${GITHUB_USERNAME}:${GITHUB_PASSWORD}@${GIT_REPO_URL}"
        //         }
        //         container(name: 'kaniko', shell: '/busybox/sh') {
        //         sh '''#!/busybox/sh
        //             ls
        //             cat /kaniko/.docker/config.json
        //             /kaniko/executor \
        //                 --context `pwd` \
        //                 --dockerfile `pwd`/Dockerfile \
        //                 --verbosity debug \
        //                 --destination egeuzma1/java-app:v${BUILD_NUMBER}
        //         '''
        //         }
        //     }
        // }
        stage('Install Ansible and Deploy') {
            steps {
                script {
                    podTemplate(label: 'python-ansible-agent', containers: [
                        containerTemplate(name: 'python', image: 'python:3.9', ttyEnabled: true, command: 'cat')
                    ]) {
                        node('python-ansible-agent') {
                            container('python') {
                                sh '''
                                # Install Ansible and the Kubernetes collection
                                pip install --no-cache-dir ansible
                                ansible-galaxy collection install kubernetes.core

                                ansible --version
                                ansible-galaxy collection list

                                '''
                            }
                        }
                    }
                }
            }
        }
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
