FROM fedora:29
COPY . /test-suite
CMD ./setup-env.sh && make run 
