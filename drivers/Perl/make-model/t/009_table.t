use Test::More;
use Test::Exception;
use Try::Tiny;
use List::MoreUtils qw/uniq/;
use File::Spec;
use lib '../lib';
use Log::Log4perl::Level;
use Bento::MakeModel;
my $samplesd = File::Spec->catdir( (-d 't' ? 't' : '.'), 'samples' );
my (@n, @r);

my $NUMNODES=29;
my $NUMNUTS=0;
my $NUMEDGES=36;
my $NUMPROPS=186;
my $NUMETYPES=15;

my $obj = Bento::MakeModel->new(
    LOG_LEVEL=>$FATAL,
    files => [ File::Spec->catdir($samplesd,"icdc-model.yml"), File::Spec->catdir($samplesd,"icdc-model-props.yml") ]
   );

my $model = $obj->model;

is scalar ($model->nodes), $NUMNODES, "count nodes";
is scalar ($model->props), $NUMPROPS, "count all props";
is scalar ($model->edge_types), $NUMETYPES, "count all edge types";
is scalar ($model->edges), $NUMEDGES, "count all edges";

my $tbl;
open my $fh, ">", \$tbl;
ok $obj->table($fh), 'make table';

my (@nodes,@relns);
my $rel;
for my $line (split /\n/,$tbl) {
  my @d = split /\t/, $line;
  next unless $d[0];
  next if ($d[0] =~ /^node/);
  if ($d[0] =~ /^relationship/) {
    $rel = 1;
    next;
  }
  if ($rel) {
    push @relns, \@d;
  }
  else {
    push @nodes, \@d;
  }
}
$DB::single=1;
is scalar (uniq map { $$_[0] } @nodes), $NUMNODES, "nodes correct";
is scalar (uniq  map { $$_[1] } @nodes), $NUMPROPS, "props correct";
is scalar @relns, $NUMEDGES, "edges correct";
is scalar (uniq map {$$_[0]} @relns), $NUMETYPES, "edge types correct";

done_testing;

