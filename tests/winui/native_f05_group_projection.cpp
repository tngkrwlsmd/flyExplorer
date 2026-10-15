#include "../../app/winui/file_group_projection.h"
#include <cassert>
#include <iostream>
using namespace fxfile::filegroup;
static Request ready(std::size_t n){return {3,3,0,0,n,true,false};}
int main(){
 std::vector<Row> rows{{42,true,true,true,L""},{17,true,false,true,L".TXT"},{19,true,false,true,L".txt"},{23,true,false,true,L".md"},{89,true,false,true,L""}};
 auto r=projectByType(ready(rows.size()),rows);
 assert(r.ready()&&r.sections.size()==4);
 assert(r.sections[0].title==L"폴더"&&r.sections[0].logicalItems[0]==42);
 assert(r.sections[1].title==L".md"&&r.sections[2].title==L".txt");
 assert((r.sections[2].logicalItems==std::vector<std::uint64_t>{17,19}));
 auto q=ready(rows.size());q.indexComplete=false;assert(projectByType(q,rows).status==Status::Incomplete);
 q=ready(rows.size());q.modelLimitReached=true;assert(projectByType(q,rows).status==Status::LimitReached);
 q=ready(rows.size());q.visibleRoute=4;assert(projectByType(q,rows).status==Status::MissingRoute);
 q=ready(rows.size());q.expectedCount++;assert(projectByType(q,rows).status==Status::WrongCount);
 rows[4].logical=19;assert(projectByType(ready(rows.size()),rows).status==Status::DuplicateIdentity);
 rows[4].logical=89;rows[4].filesystem=false;assert(projectByType(ready(rows.size()),rows).status==Status::UnsupportedItem);
 std::vector<Row> bulk;bulk.reserve(25000);
 for(std::uint64_t i=0;i<25000;i++)bulk.push_back({i,true,false,true,i%2?L".TXT":L".md"});
 auto b=projectByType(ready(bulk.size()),bulk);assert(b.ready()&&b.sections.size()==2);
 assert(b.sections[0].logicalItems.size()==12500&&b.sections[1].logicalItems.size()==12500);
 auto incomplete=ready(20000);incomplete.indexComplete=false;
 assert(projectByType(incomplete,bulk).status==Status::Incomplete);
 auto extra=ready(25001);bulk.push_back({25000,true,false,true,L".txt"});
 assert(projectByType(extra,bulk).status==Status::LimitReached);
 std::cout<<"F05_NATIVE_COMPLETE_MODEL_GROUPING_PASS\n";
}
