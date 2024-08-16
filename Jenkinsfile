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
        stage('Linting') {
            steps {
                script {
                    podTemplate(label: 'linting-agent', containers: [
                        containerTemplate(name: 'lint', image: 'python:3.9', ttyEnabled: true, command: 'cat')
                    ]) {
                        node('linting-agent') {
                            withCredentials([usernamePassword(credentialsId: 'github_credentials', usernameVariable: 'GITHUB_USERNAME', passwordVariable: 'GITHUB_PASSWORD')]) {
                                container('lint') {
                                    sh '''
                                    # Install linting tools
                                    pip install --no-cache-dir yamllint ansible-lint

                                    # Install Hadolint
                                    curl -L https://github.com/hadolint/hadolint/releases/download/v2.11.0/hadolint-Linux-x86_64 -o /usr/local/bin/hadolint
                                    chmod +x /usr/local/bin/hadolint

                                    # Run Hadolint and save output to file
                                    hadolint Dockerfile > hadolint_output.txt

                                    # Run Yamllint and save output to file
                                    yamllint . > yamllint_output.txt

                                    # Run Ansible Lint and save output to file
                                    ansible-lint ansible/playbook.yml > ansiblelint_output.txt
                                    '''
                                    // Archive the linting results
                                    archiveArtifacts artifacts: 'hadolint_output.txt,yamllint_output.txt,ansiblelint_output.txt,checkstyle_output.txt', allowEmptyArchive: true
                                }
                            }
                        }
                    }
                }
            }
        }
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
        //             /kaniko/executor \
        //                 --context `pwd` \
        //                 --dockerfile `pwd`/Dockerfile \
        //                 --destination ${DOCKERHUB_REPO}:v${BUILD_NUMBER}
        //         '''
        //         }
        //     }
        // }
        // stage('Deploy Java App with Ansible') {
        //     steps {
        //         script {
        //             podTemplate(label: 'python-ansible-agent', containers: [
        //                 containerTemplate(name: 'python', image: 'python:3.9', ttyEnabled: true, command: 'cat')
        //             ]) {
        //                 node('python-ansible-agent') {
        //                     withCredentials([usernamePassword(credentialsId: 'github_credentials', usernameVariable: 'GITHUB_USERNAME', passwordVariable: 'GITHUB_PASSWORD'),
        //                                     file(credentialsId: 'ansible-sa-kubeconfig', variable: 'KUBECONFIG')]) {
        //                         git branch: "${GIT_BRANCH}",
        //                             url: "https://${GITHUB_USERNAME}:${GITHUB_PASSWORD}@${GIT_REPO_URL}"

        //                         container('python') {
        //                             sh '''
        //                             # Install Ansible and the Kubernetes collection
        //                             pip install --no-cache-dir ansible kubernetes>=24.2.0 PyYAML>=3.11 jsonpatch
        //                             ansible-galaxy collection install kubernetes.core

        //                             ansible --version
        //                             ansible-galaxy collection list

        //                             # Use the kubeconfig file for Ansible Kubernetes tasks
        //                             export KUBECONFIG=${KUBECONFIG}
                                    
        //                             cd ansible
        //                             ansible-playbook -e kubeconfig=${KUBECONFIG} -e image_tag=v${BUILD_NUMBER} playbook.yml
        //                             '''
        //                         }
        //                     }
        //                 }
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
