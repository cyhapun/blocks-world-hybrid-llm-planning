(define (problem bw_easy_001)
  (:domain blocks-world)

  (:objects
    a b c - block
  )

  (:init
    (on_table a)
    (clear a)
    (on_table b)
    (clear b)
    (on_table c)
    (clear c)
    (handempty)
  )

  (:goal
    (on a b)
  )
)
