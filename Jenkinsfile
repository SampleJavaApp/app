pipeline {
  agent {
    kubernetes {
      label 'example-kaniko-volumes'
      yaml """
kind: Pod
metadata:
  name: kaniko
  namespace: jenkins-helm
spec:
  containers:
  - name: jnlp
    workingDir: /home/jenkins
  - name: kaniko
    workingDir: /home/jenkins
    image: gcr.io/kaniko-project/executor:debug
    imagePullPolicy: Always
    command:
    - /busybox/cat
    tty: true
    volumeMounts:
      - name: ege-secret
        mountPath: /kaniko/.docker
  volumes:
  - name: ege-secret
    projected:
      sources:
      - secret:
          name: ege-secret
          items:
            - key: .dockerconfigjson
              path: config.json
"""
    }
  }
  environment {
        DOCKERHUB_REPO = 'egeuzma1/java-app'
        GIT_REPO_URL = 'github.com/Lastroke/app.git'
        GIT_BRANCH = 'develop'
    }
  stages {
    stage('Build with Kaniko') {
      environment {
        PATH = "/busybox:/kaniko:$PATH"
      }
      steps {
        withCredentials([usernamePassword(credentialsId: 'github_credentials', usernameVariable: 'GITHUB_USERNAME', passwordVariable: 'GITHUB_PASSWORD')]) {
            git branch: "${GIT_BRANCH}",
                url: "https://${GITHUB_USERNAME}:${GITHUB_PASSWORD}@${GIT_REPO_URL}"
        }
        container(name: 'kaniko', shell: '/busybox/sh') {
          sh '''#!/busybox/sh
            ls
            cat /kaniko/.docker/config.json
            /kaniko/executor \
                --context `pwd` \
                --dockerfile `pwd`/Dockerfile \
                --verbosity debug \
                --destination egeuzma1/java-app:v3
          '''
        }
      }
    }
  }
}