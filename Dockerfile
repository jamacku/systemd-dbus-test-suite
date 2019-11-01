FROM fedora:latest
RUN dnf update -y
RUN groupadd -g 1007 testsuite-user && \
    useradd -r -u 1007 -g testsuite-user testsuite-user
USER testsuite-user
WORKDIR ~/testsuite
CMD ls ../
#RUN ./docker-install.sh 
