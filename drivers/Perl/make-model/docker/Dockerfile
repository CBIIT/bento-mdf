FROM maj1/icdc:graphviz-perlbrew

LABEL maintainer="Mark A. Jensen <mark -dot- jensen -at- nih -dot- com>"
ARG perl=perl-5.24.4
ARG vers=0.2

WORKDIR /opns
COPY / /opns/make-model
RUN /bin/bash --login -c 'perlbrew switch ${perl} ; \
 	 cd /opns/make-model/Bento-MakeModel-${vers} ; \
         perl Build.PL ; \
         ./Build ; \
         ./Build installdeps  --cpan_client "cpanm" ; \
         ./Build test ; \
	./Build install ;' \
WORKDIR /opns
COPY /start.sh .
ENTRYPOINT ["./start.sh"]
