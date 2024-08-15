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
